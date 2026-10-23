"""Phase-aware / multi-motion Reference State Initialization (RSI) for mjlab motion tracking.

Subclasses mjlab's MotionCommand (so every isinstance(..., MotionCommandCfg) check in train/play keeps working).

1) Optional per-frame prior loaded from an npz key "rsi_weight" (VLM phase prior, or dance-balance prior):
   sampling_mode (inherited field) + frame_weight_file:
     "uniform"  + prior  -> start frame ~ prior
     "adaptive" + prior  -> bin ~ (failure EMA + uniform) * bin_prior_mass**prior_power, frame in bin ~ prior
     no prior            -> original mjlab behaviour (uniform / BeyondMimic adaptive)
2) Multi-motion: if the motion npz has per-frame "clip_start"/"clip_end" (see build_multi.py), several clips are
   concatenated on one timeline. An env never steps across a clip boundary: reaching its clip's end triggers a
   resample (exactly like reaching the end of a single clip). Single-clip files behave as before.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np
import torch
from mjlab.tasks.tracking.mdp.commands import MotionCommand, MotionCommandCfg


class PhaseMotionCommand(MotionCommand):
  def __init__(self, cfg: "PhaseMotionCommandCfg", env):
    super().__init__(cfg, env)
    T = int(self.motion.time_step_total)

    # --- multi-motion bookkeeping ---
    d = np.load(cfg.motion_file)
    if "clip_end" in d.files:
      self.clip_start = torch.tensor(d["clip_start"], dtype=torch.long, device=self.device)
      self.clip_end = torch.tensor(d["clip_end"], dtype=torch.long, device=self.device)
      self.clip_id = torch.tensor(d["clip_id"], dtype=torch.long, device=self.device)
      self.clip_names = [str(x) for x in d["clip_names"]]
      print(f"[MultiMotion] {len(self.clip_names)} clips, {T} frames: {self.clip_names}")
    else:
      self.clip_start = torch.zeros(T, dtype=torch.long, device=self.device)
      self.clip_end = torch.full((T,), T, dtype=torch.long, device=self.device)
      self.clip_id = torch.zeros(T, dtype=torch.long, device=self.device)
      self.clip_names = ["clip"]
    self.cur_end = torch.full((self.num_envs,), T, dtype=torch.long, device=self.device)
    # a start frame must leave at least one step inside its clip
    self.valid_start = (torch.arange(T, device=self.device) < self.clip_end - 1).float()

    # --- optional frame prior ---
    self.frame_prior = None
    if cfg.frame_weight_file:
      w = np.load(cfg.frame_weight_file)["rsi_weight"].astype(np.float64)
      if len(w) != T:  # labels were resampled to the npz timeline, but be robust to off-by-one
        w = np.interp(np.linspace(0, 1, T), np.linspace(0, 1, len(w)), w)
      w = np.maximum(w, cfg.prior_floor * w.mean())  # never make a frame unreachable
      self.frame_prior = torch.tensor(w / w.sum(), dtype=torch.float32, device=self.device)
    base = self.frame_prior if self.frame_prior is not None else torch.full((T,), 1.0 / T, device=self.device)
    base = base * self.valid_start
    self.frame_prior_eff = base / base.sum()
    bin_of = torch.clamp((torch.arange(T, device=self.device) * self.bin_count) // T, 0, self.bin_count - 1)
    self.bin_mass = torch.zeros(self.bin_count, device=self.device).index_add_(0, bin_of, self.frame_prior_eff)
    in_bin = torch.zeros(self.bin_count, T, device=self.device)
    in_bin[bin_of, torch.arange(T, device=self.device)] = self.frame_prior_eff
    self.in_bin = in_bin / in_bin.sum(dim=1, keepdim=True).clamp_min(1e-12)
    if self.frame_prior is not None:
      ent = -(self.frame_prior * (self.frame_prior + 1e-12).log()).sum() / math.log(T)
      print(f"[PhaseRSI] prior from {cfg.frame_weight_file}: T={T}, bins={self.bin_count}, "
            f"normalised entropy={float(ent):.3f}, mode={cfg.sampling_mode}")

  # ---------------- sampling ----------------
  def _uniform_sampling(self, env_ids: torch.Tensor):
    self.time_steps[env_ids] = torch.multinomial(self.frame_prior_eff, len(env_ids), replacement=True)
    p = self.bin_mass
    self.metrics["sampling_entropy"][:] = -(p * (p + 1e-12).log()).sum() / max(math.log(self.bin_count), 1e-12)
    pmax, imax = p.max(dim=0)
    self.metrics["sampling_top1_prob"][:] = pmax
    self.metrics["sampling_top1_bin"][:] = imax.float() / self.bin_count

  def _adaptive_sampling(self, env_ids: torch.Tensor):
    episode_failed = self._env.termination_manager.terminated[env_ids]
    if torch.any(episode_failed):
      cur = torch.clamp((self.time_steps * self.bin_count) // max(self.motion.time_step_total, 1), 0, self.bin_count - 1)
      self._current_bin_failed[:] = torch.bincount(cur[env_ids][episode_failed], minlength=self.bin_count)
    p = self.bin_failed_count + self.cfg.adaptive_uniform_ratio / float(self.bin_count)
    p = torch.nn.functional.pad(p[None, None], (0, self.cfg.adaptive_kernel_size - 1), mode="replicate")
    p = torch.nn.functional.conv1d(p, self.kernel.view(1, 1, -1)).view(-1)
    p = p * self.bin_mass.pow(self.cfg.prior_power if self.frame_prior is not None else 1.0)
    p = p * (self.bin_mass > 0)
    p = p / p.sum()
    bins = torch.multinomial(p, len(env_ids), replacement=True)
    self.time_steps[env_ids] = torch.multinomial(self.in_bin[bins], 1).squeeze(1)
    H = -(p * (p + 1e-12).log()).sum()
    self.metrics["sampling_entropy"][:] = H / math.log(self.bin_count) if self.bin_count > 1 else 1.0
    pmax, imax = p.max(dim=0)
    self.metrics["sampling_top1_prob"][:] = pmax
    self.metrics["sampling_top1_bin"][:] = imax.float() / self.bin_count

  def _resample_command(self, env_ids: torch.Tensor):
    if self.cfg.sampling_mode == "start":  # play: start of the first clip
      self.time_steps[env_ids] = 0
      self.cur_end[env_ids] = self.clip_end[0]
      # parent writes the reference state for these envs (its "start" branch sets time_steps=0 again)
      return super()._resample_command(env_ids)
    super()._resample_command(env_ids)  # samples time_steps (via the methods above) and writes the state
    self.cur_end[env_ids] = self.clip_end[self.time_steps[env_ids]]

  def _update_command(self):
    # Envs about to step past their clip end: push them to the global end so the parent resamples them.
    crossing = (self.time_steps + 1) >= self.cur_end
    if torch.any(crossing):
      self.time_steps[crossing] = self.motion.time_step_total - 1
    super()._update_command()


@dataclass(kw_only=True)
class PhaseMotionCommandCfg(MotionCommandCfg):
  frame_weight_file: str | None = None
  prior_power: float = 1.0
  prior_floor: float = 0.05

  def build(self, env) -> PhaseMotionCommand:
    return PhaseMotionCommand(self, env)
