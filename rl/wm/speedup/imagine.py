"""Imagined tracking env: the frozen world model as dynamics, mjlab's Unitree-G1-Tracking-No-State-Estimation actor
observation, tracking reward and terminations recomputed exactly on FK body poses (body velocities via jvp of the
FK). Everything is differentiable for BPTT. The task constants (default pose, action scale, soft limits, weights,
thresholds) come from spec.json, written by record.py from the real mjlab env.
Order per step, as in mjlab: action -> dynamics -> time step + 1 -> reward / termination on the new state -> obs."""
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
import wm  # noqa: E402
from fk import G1FK, quat_to_mat  # noqa: E402

DT = 0.02


def skew(w):
  z = torch.zeros_like(w[..., 0])
  return torch.stack([z, -w[..., 2], w[..., 1], w[..., 2], z, -w[..., 0], -w[..., 1], w[..., 0], z], -1).reshape(w.shape[:-1] + (3, 3))


def rot_angle_sq(Ra, Rb):
  """squared angle of Ra^T Rb, smooth at 0 (atan2 form, no acos)"""
  M = Ra.transpose(-1, -2) @ Rb
  v = torch.stack([M[..., 2, 1] - M[..., 1, 2], M[..., 0, 2] - M[..., 2, 0], M[..., 1, 0] - M[..., 0, 1]], -1)
  s = torch.sqrt((v * v).sum(-1) + 1e-12) / 2
  c = (M.diagonal(dim1=-2, dim2=-1).sum(-1) - 1) / 2
  return torch.atan2(s, c) ** 2


def yaw_only(R):
  return wm.rot_z(torch.atan2(R[..., 1, 0], R[..., 0, 0]))


class Policy(torch.nn.Module):
  """rsl_rl actor (obs normaliser + ELU MLP), deterministic mean action"""
  def __init__(self, ckpt, device):
    super().__init__()
    sd = torch.load(ckpt, map_location=device, weights_only=False)["actor_state_dict"]
    self.mean, self.std = sd["obs_normalizer._mean"], sd["obs_normalizer._std"]
    W = sorted({int(k.split(".")[1]) for k in sd if k.startswith("mlp.")})
    layers = []
    for i, li in enumerate(W):
      lin = torch.nn.Linear(*sd[f"mlp.{li}.weight"].shape[::-1])
      lin.weight.data.copy_(sd[f"mlp.{li}.weight"]); lin.bias.data.copy_(sd[f"mlp.{li}.bias"])
      layers += [lin] + ([torch.nn.ELU()] if i < len(W) - 1 else [])
    self.mlp = torch.nn.Sequential(*layers).to(device)
    self.sd = sd

  def forward(self, obs):
    return self.mlp((obs - self.mean) / (self.std + 1e-2))

  def export(self, path, template_ckpt):
    """write the trained weights back into an rsl_rl checkpoint (mjlab eval loads it unchanged)"""
    ck = torch.load(template_ckpt, map_location="cpu", weights_only=False)
    W = sorted({int(k.split(".")[1]) for k in ck["actor_state_dict"] if k.startswith("mlp.")})
    lins = [m for m in self.mlp if isinstance(m, torch.nn.Linear)]
    for li, lin in zip(W, lins):
      ck["actor_state_dict"][f"mlp.{li}.weight"] = lin.weight.detach().cpu().clone()
      ck["actor_state_dict"][f"mlp.{li}.bias"] = lin.bias.detach().cpu().clone()
    torch.save(ck, path)


class Reference:
  def __init__(self, motion, robot_bodies, device):
    z = np.load(motion)
    f = lambda k: torch.tensor(z[k], dtype=torch.float32, device=device)
    self.jp, self.jv = f("joint_pos"), f("joint_vel")
    self.bp, self.bR = f("body_pos_w"), quat_to_mat(f("body_quat_w"))
    self.bv, self.bw = f("body_lin_vel_w"), f("body_ang_vel_w")
    self.T = self.jp.shape[0]
    self.names = list(robot_bodies)


class ImaginedTracking:
  def __init__(self, model, spec_path, motion, xi, device="cuda", max_delay=0):
    spec = json.loads(Path(spec_path).read_text())
    self.spec, self.dev, self.model = spec, device, model
    t = lambda k: torch.tensor(spec[k], dtype=torch.float32, device=device)
    self.default_q, self.lim = t("default_joint_pos"), t("soft_joint_pos_limits")  # (29,), (29, 2)
    self.fk = G1FK(spec["joint_names"], device)
    self.ref = Reference(motion, spec["robot_body_names"], device)
    fk_idx = {n: i for i, n in enumerate(self.fk.names[1:])}  # FK output = robot bodies (world left out)
    self.fk_track = [fk_idx[n] for n in spec["tracked_bodies"]]
    self.ref_track = [self.ref.names.index(n) for n in spec["tracked_bodies"]]
    self.a_fk, self.a_ref = fk_idx[spec["anchor_body"]], self.ref.names.index(spec["anchor_body"])
    self.ee = [spec["tracked_bodies"].index(n) for n in spec["ee_bodies"]]
    self.w, self.std, self.thr = spec["reward_weights"], spec["reward_std"], spec["term_thresholds"]
    self.xi = torch.tensor(xi, dtype=torch.float32, device=device)
    self.max_delay = max_delay

  # ---------- state ----------
  def reset_from_reference(self, frames):
    """RSI without noise: the robot at the reference state of the given frames"""
    r, fr = self.ref, frames
    R = r.bR[fr, 0]
    yaw = torch.atan2(R[:, 1, 0], R[:, 0, 0])
    Rrel = wm.rot_z(yaw).transpose(-1, -2) @ R
    q = torch.maximum(torch.minimum(r.jp[fr], self.lim[:, 1]), self.lim[:, 0])
    s = torch.cat([r.bp[fr, 0, 2:3], wm.mat_to_six(Rrel), (R.transpose(-1, -2) @ r.bv[fr, 0].unsqueeze(-1)).squeeze(-1),
                   (R.transpose(-1, -2) @ r.bw[fr, 0].unsqueeze(-1)).squeeze(-1), q, r.jv[fr]], -1)
    return self.make_state(s, r.bp[fr, 0, :2], yaw, frames)

  def make_state(self, s, xy, yaw, frames, last_act=None, delay=None):
    N = s.shape[0]
    z = torch.zeros(N, wm.NJ, device=self.dev)
    return {"s": s, "xy": xy, "yaw": yaw, "t": frames.clone(), "last": z if last_act is None else last_act,
            "hist": z.unsqueeze(0).repeat(self.max_delay + 1, 1, 1),
            "delay": torch.zeros(N, dtype=torch.long, device=self.dev) if delay is None else delay}

  def kin(self, st):
    """world poses + velocities of all bodies (exact; batched FK with analytic velocity propagation)"""
    s = st["s"]
    Rr = wm.rot_z(st["yaw"]) @ wm.six_to_mat(s[:, 1:7])
    pr = torch.cat([st["xy"], s[:, :1]], -1)
    v, w = (Rr @ s[:, 7:10].unsqueeze(-1)).squeeze(-1), (Rr @ s[:, 10:13].unsqueeze(-1)).squeeze(-1)
    q, qd = s[:, 13:13 + wm.NJ], s[:, 13 + wm.NJ:]
    P, R, V, W = self.fk.with_vel(pr, Rr, v, w, q, qd)
    return {"P": P, "R": R, "V": V, "W": W, "w_b": s[:, 10:13], "q": q, "qd": qd}

  def kin_jvp(self, st):
    """reference implementation of kin: per-body FK, velocities by jvp (slow; used to check kin)"""
    s = st["s"]
    Rr = wm.rot_z(st["yaw"]) @ wm.six_to_mat(s[:, 1:7])
    pr = torch.cat([st["xy"], s[:, :1]], -1)
    v, w = (Rr @ s[:, 7:10].unsqueeze(-1)).squeeze(-1), (Rr @ s[:, 10:13].unsqueeze(-1)).squeeze(-1)
    q, qd = s[:, 13:13 + wm.NJ], s[:, 13 + wm.NJ:]
    (P, R), (dP, dR) = torch.func.jvp(self.fk, (pr, Rr, q), (v, skew(w) @ Rr, qd))
    W = dR @ R.transpose(-1, -2)
    om = torch.stack([W[..., 2, 1] - W[..., 1, 2], W[..., 0, 2] - W[..., 2, 0], W[..., 1, 0] - W[..., 0, 1]], -1) / 2
    return {"P": P, "R": R, "V": dP, "W": om, "w_b": s[:, 10:13], "q": q, "qd": qd}

  # ---------- task ----------
  def obs(self, st, k=None):
    k = k or self.kin(st)
    t, r = st["t"], self.ref
    Ra, Rref = k["R"][:, self.a_fk], r.bR[t, self.a_ref]
    ori = (Ra.transpose(-1, -2) @ Rref)[..., :2].reshape(-1, 6)
    return torch.cat([r.jp[t], r.jv[t], ori, k["w_b"], k["q"] - self.default_q, k["qd"], st["last"]], -1)

  def reward_terms(self, st, act, prev_act, k=None):
    k = k or self.kin(st)
    t, r = st["t"], self.ref
    pa, Ra = k["P"][:, self.a_fk], k["R"][:, self.a_fk]
    ref_pa, ref_Ra = r.bp[t, self.a_ref], r.bR[t, self.a_ref]
    dR = yaw_only(Ra @ ref_Ra.transpose(-1, -2))
    dpos = torch.cat([pa[:, :2], ref_pa[:, 2:3]], -1)
    rb = r.bp[t][:, self.ref_track]
    rel_p = dpos[:, None] + (dR[:, None] @ (rb - ref_pa[:, None]).unsqueeze(-1)).squeeze(-1)
    rel_R = dR[:, None] @ r.bR[t][:, self.ref_track]
    P, R = k["P"][:, self.fk_track], k["R"][:, self.fk_track]
    sd = self.std
    out = {
      "motion_global_root_pos": torch.exp(-((ref_pa - pa) ** 2).sum(-1) / sd["motion_global_root_pos"] ** 2),
      "motion_global_root_ori": torch.exp(-rot_angle_sq(ref_Ra, Ra) / sd["motion_global_root_ori"] ** 2),
      "motion_body_pos": torch.exp(-((rel_p - P) ** 2).sum(-1).mean(-1) / sd["motion_body_pos"] ** 2),
      "motion_body_ori": torch.exp(-rot_angle_sq(rel_R, R).mean(-1) / sd["motion_body_ori"] ** 2),
      "motion_body_lin_vel": torch.exp(-((r.bv[t][:, self.ref_track] - k["V"][:, self.fk_track]) ** 2).sum(-1).mean(-1)
                                       / sd["motion_body_lin_vel"] ** 2),
      "motion_body_ang_vel": torch.exp(-((r.bw[t][:, self.ref_track] - k["W"][:, self.fk_track]) ** 2).sum(-1).mean(-1)
                                       / sd["motion_body_ang_vel"] ** 2),
      "action_rate_l2": ((act - prev_act) ** 2).sum(-1),
      "joint_limit": ((self.lim[:, 0] - k["q"]).clamp(min=0) + (k["q"] - self.lim[:, 1]).clamp(min=0)).sum(-1),
    }
    return {n: v * self.w[n] for n, v in out.items() if n in self.w}

  def terminated(self, st, k=None):
    k = k or self.kin(st)
    t, r, th = st["t"], self.ref, self.thr
    za = (r.bp[t, self.a_ref, 2] - k["P"][:, self.a_fk, 2]).abs() > th["anchor_pos"]
    zo = (r.bR[t, self.a_ref][:, 2, 2] - k["R"][:, self.a_fk][:, 2, 2]).abs() > th["anchor_ori"]
    ee_ref = r.bp[t][:, self.ref_track][:, self.ee, 2]
    ze = ((ee_ref - k["P"][:, self.fk_track][:, self.ee, 2]).abs() > th["ee_body_pos"]).any(-1)
    return za | zo | ze

  def step(self, st, act):
    """-> new state, reward terms (weighted, not scaled by dt), terminated, kinematics. The clip end is not a
    termination (mjlab resamples the command and the episode goes on): the caller treats t == T - 1 as truncation."""
    hist = torch.cat([act[None], st["hist"][:-1]])
    use = hist[st["delay"], torch.arange(act.shape[0], device=self.dev)]
    s1, dr = self.model.step(st["s"], use, self.xi.expand(act.shape[0], 3))
    c, sn = torch.cos(st["yaw"]), torch.sin(st["yaw"])
    xy = st["xy"] + torch.stack([c * dr[:, 1] - sn * dr[:, 2], sn * dr[:, 1] + c * dr[:, 2]], -1)
    t1 = (st["t"] + 1).clamp(max=self.ref.T - 1)
    new = {"s": s1, "xy": xy, "yaw": st["yaw"] + dr[:, 0], "t": t1, "last": act, "hist": hist, "delay": st["delay"]}
    k = self.kin(new)
    rew = self.reward_terms(new, act, st["last"], k)
    return new, rew, self.terminated(new, k), k
