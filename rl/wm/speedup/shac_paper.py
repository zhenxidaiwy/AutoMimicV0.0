"""Plan A: the SuperMimic policy update (§3, Alg. A.1, Table A.5) through the frozen world model, offline buffer.
Per iteration:
  - N start states drawn from a replay buffer of real mjlab states (record.py real.npz: state, frame, previous action);
  - H imagined steps; sensor noise (mjlab's Unoise ranges) added to the predicted noise-free observation;
  - J = sum_t gamma^t c_t r_{t+1} + gamma^H c_H V(s_H, g_H, xi), soft survival c_{t+1} = c_t (1 - d_{t+1});
  - actor: Adam (0.9, 0.95), lr 2e-4, global grad-norm clip 1.0 then element-wise 0.1;
  - critic V(s, g, xi), MLP (256, 128), GAE(lambda 0.95) targets computed once per rollout, 5 epochs x 4 minibatches,
    no target network, same optimiser settings.
Deviations (also in SUPERMIMIC_NOTES.md):
  - d is an analytic soft margin on mjlab's termination checks, sigmoid((err - thr) / (tau thr)), not a learned head;
  - the buffer is fixed (Plan B refreshes it online), the actor is a PPO checkpoint, not from scratch;
  - the clip end (240 frames) truncates: value bootstrap there, later steps masked;
  - constant lr (the paper's cosine schedule spans 250 k iterations);
  - the goal g is the reference at t: joint pos / vel, anchor orientation in the robot frame, anchor height, phase.
The update itself (Updater) is shared with online.py (Plan B).
Usage: python shac_paper.py --spec <dir> --wm <wm.pt> --init <model.pt> --motion <clip.npz> --buffer <real.npz>[,...]
  --out <dir> [--envs 4096] [--H 32] [--minutes 30] [--export-min 5]"""
import argparse
import json
import time
from pathlib import Path

import numpy as np
import torch

import imagine as im
from check import real_states

# mjlab Unitree-G1-Tracking-No-State-Estimation actor obs: ref jp 0:29, ref jv 29:58, anchor ori 58:64,
# base ang vel 64:67, joint pos 67:96, joint vel 96:125, last action 125:154 (tracking_env_cfg.py Unoise ranges)
NOISE = [(58, 64, 0.05), (64, 67, 0.2), (67, 96, 0.01), (96, 125, 0.5)]


class Buffer:
  """real mjlab states usable as rollout starts: the previous step exists and is the same episode"""
  def __init__(self, paths, T, dev):
    S, XY, YAW, FR, LAST = [], [], [], [], []
    for p in paths:
      z = np.load(p)
      s, xy, yaw = real_states(z, dev)
      fr = torch.tensor(z["frame"], dtype=torch.long, device=dev)
      act = torch.tensor(z["action"], device=dev)
      ok = (fr[1:] == fr[:-1] + 1) & (fr[1:] < T - 1)
      t, n = ok.nonzero(as_tuple=True)
      t = t + 1
      S.append(s[t, n]); XY.append(xy[t, n]); YAW.append(yaw[t, n]); FR.append(fr[t, n]); LAST.append(act[t - 1, n])
    self.s, self.xy, self.yaw, self.fr, self.last = (torch.cat(x) for x in (S, XY, YAW, FR, LAST))
    self.n = len(self.fr)

  def sample(self, env, n, gen):
    i = torch.randint(0, self.n, (n,), device=self.fr.device, generator=gen)
    return env.make_state(self.s[i], self.xy[i], self.yaw[i], self.fr[i], last_act=self.last[i])


class Critic(torch.nn.Module):
  def __init__(self, dim, mean, std):
    super().__init__()
    self.mean, self.std = mean, std
    self.mlp = torch.nn.Sequential(torch.nn.Linear(dim, 256), torch.nn.ELU(), torch.nn.Linear(256, 128),
                                   torch.nn.ELU(), torch.nn.Linear(128, 1))

  def forward(self, x):
    return self.mlp((x - self.mean) / (self.std + 1e-2)).squeeze(-1)


def soft_done(env, st, k, tau):
  """analytic soft version of mjlab's three termination checks (z-only anchor, anchor R22, ee z)"""
  t, r, th = st["t"], env.ref, env.thr
  e = [((r.bp[t, env.a_ref, 2] - k["P"][:, env.a_fk, 2]).abs(), th["anchor_pos"]),
       ((r.bR[t, env.a_ref][:, 2, 2] - k["R"][:, env.a_fk][:, 2, 2]).abs(), th["anchor_ori"])]
  ee_ref = r.bp[t][:, env.ref_track][:, env.ee, 2]
  e.append(((ee_ref - k["P"][:, env.fk_track][:, env.ee, 2]).abs(), th["ee_body_pos"]))
  keep = 1.0
  for err, thr in e:
    p = torch.sigmoid((err - thr) / (tau * thr))
    keep = keep * ((1 - p).prod(-1) if p.dim() > 1 else (1 - p))
  return 1 - keep


class Updater:
  """one SuperMimic policy + critic update from given imagined start states (the env holds the frozen model).
  a: gamma, lam, H, lr, clip, clip_elem, critic_epochs, critic_mb, obs_noise, tau, no_critic, hand_friction."""
  def __init__(self, env, pol, a, gen, x_stats):
    self.env, self.pol, self.a, self.gen = env, pol, a, gen
    self.dev = env.dev
    self.xi = torch.tensor([1.0, 1.0, a.hand_friction], device=self.dev)
    x0 = self.critic_in(x_stats, env.obs(x_stats))
    self.critic = Critic(x0.shape[1], x0.mean(0), x0.std(0)).to(self.dev)
    betas = (0.9, 0.95)
    self.opt_a = torch.optim.Adam(pol.mlp.parameters(), lr=a.lr, betas=betas)
    self.opt_c = torch.optim.Adam(self.critic.parameters(), lr=a.lr, betas=betas)
    self.nscale = torch.zeros(154, device=self.dev)
    for i0, i1, v in NOISE:
      self.nscale[i0:i1] = v * a.obs_noise
    # optional learned heads (online.py, harness mode): heads(x_t, a_t) -> (reward residual of the step, termination
    # logit of the step), added to the analytic reward / combined with the analytic soft termination
    self.heads = None
    self.guard = {"nonfinite_rollouts": 0, "skip_actor": 0, "skip_critic": 0}  # numerical guards (counts)

  def critic_in(self, st, o):
    # (s, g, xi): world-model state, goal = reference at t, sim context
    env, t = self.env, st["t"]
    T = env.ref.T
    g = torch.cat([o[:, :64], env.ref.bp[t, env.a_ref, 2:3], (t.float() / T)[:, None]], -1)
    return torch.cat([st["s"], g, self.xi.expand(len(t), 3)], -1)

  def noisy(self, o):
    return o + self.nscale * (2 * torch.rand(o.shape, device=self.dev, generator=self.gen) - 1)

  def probe(self, st0):
    # mean imagined per-step tracking reward over H steps from fixed starts, no noise, hard terminations
    env, n = self.env, len(st0["t"])
    with torch.no_grad():
      s_, o_, ret_, al_ = dict(st0), env.obs(st0), 0.0, torch.ones(n, device=self.dev)
      for _ in range(self.a.H):
        s_, rr_, te_, k_ = env.step(s_, self.pol(o_))
        o_ = env.obs(s_, k_)
        ret_ = ret_ + al_ * sum(rr_.values())
        al_ = al_ * (~te_).float()
      return round((ret_ / self.a.H).mean().item(), 4)

  def update(self, st, actor_on=True):
    a, env, pol, critic, dev = self.a, self.env, self.pol, self.critic, self.dev
    g, lam, H, T = a.gamma, a.lam, a.H, env.ref.T
    N = len(st["t"])
    o = env.obs(st)
    c = torch.ones(N, device=dev)       # soft survival
    live = torch.ones(N, device=dev)    # 0 after the clip end (truncated, bootstrapped)
    ret = torch.zeros(N, device=dev)
    X, R, Dn, M, TR = [], [], [], [], []
    n_hard = torch.zeros(N, dtype=torch.bool, device=dev)
    with torch.set_grad_enabled(actor_on):
      for h in range(H):
        x_t = self.critic_in(st, o)
        X.append(x_t.detach()); M.append(live.detach())
        act = pol(self.noisy(o) if a.obs_noise > 0 else o)
        if self.heads is not None:
          r_res, d_logit = self.heads(x_t, act)
        trunc = (st["t"] + 1 >= T - 1).float() * live
        st, rr, term, k = env.step(st, act)
        rew = sum(rr.values())
        if self.heads is not None:
          rew = rew + r_res
        rew = rew * im.DT
        o = env.obs(st, k)
        d = soft_done(env, st, k, a.tau)
        if self.heads is not None:
          d = 1 - (1 - d) * (1 - torch.sigmoid(d_logit))
        ret = ret + (g ** h) * live * c * rew
        c = c * (1 - d)
        if trunc.any() and not a.no_critic:
          ret = ret + (g ** (h + 1)) * (trunc * c) * critic(self.critic_in(st, o)).detach()
        R.append(rew.detach()); Dn.append(d.detach()); TR.append(trunc)
        n_hard |= term & (live > 0)
        live = live * (1 - trunc)
      xH = self.critic_in(st, o)
      vH = 0.0 if a.no_critic else critic(xH)
      J = ret + (g ** H) * live * c * vH
      fin = torch.isfinite(J)  # an imagined rollout that diverged is dropped, not averaged in
      self.guard["nonfinite_rollouts"] += int((~fin).sum())
      loss_a = -torch.where(fin, J, torch.zeros_like(J)).sum() / fin.sum().clamp(min=1) / H
    rec = {}
    if actor_on:
      self.opt_a.zero_grad(set_to_none=True)
      loss_a.backward()
      gn = torch.nn.utils.clip_grad_norm_(pol.mlp.parameters(), a.clip)
      if torch.isfinite(gn):
        torch.nn.utils.clip_grad_value_(pol.mlp.parameters(), a.clip_elem)
        self.opt_a.step()
      else:
        self.guard["skip_actor"] += 1
      rec["grad_norm"] = round(gn.item(), 3)
    # critic: GAE(lambda) targets, once per rollout; truncation bootstraps V(next) and cuts the lambda chain
    with torch.no_grad():
      Xs = torch.stack(X)
      V = torch.stack([critic(Xs[h]) for h in range(H)] + [critic(xH.detach())])
      tgt = torch.zeros(H, N, device=dev)
      adv = torch.zeros(N, device=dev)
      for h in reversed(range(H)):
        cont = (1 - Dn[h]) * (1 - TR[h])
        delta = R[h] + g * (1 - Dn[h]) * V[h + 1] - V[h]
        adv = delta + g * lam * cont * adv
        tgt[h] = adv + V[h]
      m = (torch.stack(M) > 0) & torch.isfinite(tgt) & torch.isfinite(Xs).all(-1)
      xs, ys = Xs[m], tgt[m]
    lc = torch.zeros(())
    for _ in range(0 if a.no_critic else a.critic_epochs):
      perm = torch.randperm(len(ys), device=dev)
      for j in perm.chunk(a.critic_mb):
        lc = ((critic(xs[j]) - ys[j]) ** 2).mean()
        self.opt_c.zero_grad(set_to_none=True); lc.backward()
        if torch.isfinite(torch.nn.utils.clip_grad_norm_(critic.parameters(), a.clip)):
          self.opt_c.step()
        else:
          self.guard["skip_critic"] += 1
    rec.update({"rew_step": round(torch.stack(R).mean().item() / im.DT, 4), "surv_H": round(c.mean().item(), 4),
                "hard_term": round(n_hard.float().mean().item(), 4), "trunc": round(1 - live.mean().item(), 3),
                "critic_loss": round(lc.item(), 6)})
    return rec


def main(a):
  dev = "cuda"
  torch.manual_seed(a.seed)
  out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
  model, _ = im.wm.load(a.wm, dev)
  model.eval()
  for p in model.parameters():
    p.requires_grad_(False)
  env = im.ImaginedTracking(model, Path(a.spec) / "spec.json", a.motion, [1.0, 1.0, a.hand_friction], dev)
  buf = Buffer(a.buffer.split(","), env.ref.T, dev)
  pol = im.Policy(a.init, dev)
  gen = torch.Generator(device=dev).manual_seed(a.seed)
  up = Updater(env, pol, a, gen, buf.sample(env, 8192, gen))
  st_probe = buf.sample(env, 2048, torch.Generator(device=dev).manual_seed(123))
  t0, it, next_export, log = time.time(), 0, 0.0, []
  while (time.time() - t0) / 60 < a.minutes:
    it += 1
    actor_on = it > a.warmup
    rec = up.update(buf.sample(env, a.envs, gen), actor_on)
    mins = (time.time() - t0) / 60
    rec = {"it": it, "min": round(mins, 2), **rec, "actor_on": actor_on}
    if it % a.probe_every == 0 or it == 1:
      rec["probe_rew_step"] = up.probe(st_probe)
    log.append(rec)
    if it % a.log_every == 0:
      print(json.dumps(rec), flush=True)
    if actor_on and mins >= next_export:
      pol.export(out / f"model_wm_{mins:05.1f}min.pt", a.init)
      next_export = mins + a.export_min
  pol.export(out / f"model_wm_{(time.time() - t0) / 60:05.1f}min.pt", a.init)
  (out / "log.json").write_text(json.dumps({"args": vars(a), "buffer_states": buf.n, "log": log}))
  print(json.dumps({"done": True, "iters": it, "min": round((time.time() - t0) / 60, 1), "buffer_states": buf.n,
                    "peak_mem_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)}), flush=True)


def add_update_args(ap):
  ap.add_argument("--H", type=int, default=32)
  ap.add_argument("--gamma", type=float, default=0.99)
  ap.add_argument("--lam", type=float, default=0.95)
  ap.add_argument("--lr", type=float, default=2e-4)
  ap.add_argument("--clip", type=float, default=1.0)
  ap.add_argument("--clip-elem", type=float, default=0.1)
  ap.add_argument("--critic-epochs", type=int, default=5)
  ap.add_argument("--critic-mb", type=int, default=4)
  ap.add_argument("--obs-noise", type=float, default=1.0, help="scale of mjlab's sensor-noise ranges (0 = off)")
  ap.add_argument("--tau", type=float, default=0.1, help="soft-termination width, fraction of each threshold")
  ap.add_argument("--hand-friction", type=float, default=0.6)
  ap.add_argument("--no-critic", action="store_true", help="ablation: plain H-step return (paper §4.3)")


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--spec", required=True)
  ap.add_argument("--wm", required=True)
  ap.add_argument("--init", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--buffer", required=True, help="comma-separated record.py real.npz files")
  ap.add_argument("--out", required=True)
  ap.add_argument("--envs", type=int, default=4096)
  ap.add_argument("--minutes", type=float, default=30)
  ap.add_argument("--export-min", type=float, default=5)
  ap.add_argument("--warmup", type=int, default=0, help="critic-only iterations first (paper: none)")
  ap.add_argument("--log-every", type=int, default=10)
  ap.add_argument("--probe-every", type=int, default=10)
  ap.add_argument("--seed", type=int, default=0)
  add_update_args(ap)
  main(ap.parse_args())
