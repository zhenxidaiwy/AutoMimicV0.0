"""S3: policy update by backprop through the frozen world model (SHAC: H-step imagined rollouts + a critic for the
value beyond H). The actor starts from a PPO checkpoint and is exported back into that checkpoint format, so the
unchanged mjlab eval scores it. Wall time is logged from the start (critic warm-up included).
Usage: python shac.py --spec <dir with spec.json> --wm <wm.pt> --init <model.pt> --motion <clip.npz> --out <dir>
  [--envs 1024] [--H 32] [--minutes 30] [--export-min 5]"""
import argparse
import json
import time
from pathlib import Path

import torch

import imagine as im


class Critic(torch.nn.Module):
  def __init__(self, pol, T):
    super().__init__()
    self.mean, self.std, self.T = pol.mean, pol.std, T
    dims = [154 + 1, 512, 256, 128, 1]
    layers = []
    for i in range(len(dims) - 1):
      layers += [torch.nn.Linear(dims[i], dims[i + 1])] + ([torch.nn.ELU()] if i < len(dims) - 2 else [])
    self.mlp = torch.nn.Sequential(*layers)

  def forward(self, obs, t):
    return self.mlp(torch.cat([(obs - self.mean) / (self.std + 1e-2), (t.float() / self.T)[:, None]], -1)).squeeze(-1)


def main(a):
  dev = "cuda"
  torch.manual_seed(a.seed)
  out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
  model, _ = im.wm.load(a.wm, dev)
  model.eval()
  for p in model.parameters():
    p.requires_grad_(False)
  env = im.ImaginedTracking(model, Path(a.spec) / "spec.json", a.motion, [1.0, 1.0, a.hand_friction], dev)
  T = env.ref.T
  pol = im.Policy(a.init, dev)
  critic = Critic(pol, T).to(dev)
  opt_a = (torch.optim.SGD(pol.mlp.parameters(), lr=a.lr_actor) if a.sgd
           else torch.optim.Adam(pol.mlp.parameters(), lr=a.lr_actor))
  opt_c = torch.optim.Adam(critic.parameters(), lr=a.lr_critic)
  gen = torch.Generator(device=dev).manual_seed(a.seed)
  rsi = lambda n: env.reset_from_reference(torch.randint(0, T - 1, (n,), device=dev, generator=gen))
  st = rsi(a.envs)
  g, lam, H, N = a.gamma, a.lam, a.H, a.envs
  # fixed probe batch: imagined H-step return of the current policy, comparable across iterations
  st_probe = env.reset_from_reference(torch.randint(0, T - H - 1, (2048,), device=dev,
                                                    generator=torch.Generator(device=dev).manual_seed(123)))

  def probe():
    with torch.no_grad():
      s_, o_, ret_, al_ = dict(st_probe), env.obs(st_probe), 0.0, torch.ones(2048, device=dev)
      for _ in range(H):
        s_, rr_, te_, k_ = env.step(s_, pol(o_))
        o_ = env.obs(s_, k_)
        ret_ = ret_ + al_ * sum(rr_.values())
        al_ = al_ * (~te_).float()
      return round((ret_ / H).mean().item(), 4)

  if a.no_critic:
    a.warmup = 0
  t0, it, next_export, log = time.time(), 0, 0.0, []
  while (time.time() - t0) / 60 < a.minutes:
    it += 1
    actor_on = it > a.warmup
    st = rsi(N) if a.fresh else {k: v.detach() for k, v in st.items()}
    o = env.obs(st)
    alive = torch.ones(N, device=dev)
    ret = torch.zeros(N, device=dev)
    n_term = torch.zeros(N, dtype=torch.bool, device=dev)
    n_trunc = torch.zeros(N, dtype=torch.bool, device=dev)
    O, TT, R, D, A = [], [], [], [], []  # for the critic: obs, time, reward, done (term), alive-before
    with torch.set_grad_enabled(actor_on):
      for h in range(H):
        O.append(o.detach()); TT.append(st["t"]); A.append(alive.detach())
        act = pol(o)
        if a.noise > 0:
          act = act + a.noise * torch.randn(act.shape, device=dev, generator=gen)
        trunc = st["t"] + 1 >= T - 1
        st, rr, term, k = env.step(st, act)
        r = sum(rr.values()) * im.DT
        o = env.obs(st, k)
        ret = ret + (g ** h) * alive * r
        # clip end: bootstrap with the critic (mjlab resamples the command, the episode goes on)
        tr_now = trunc & ~term & (alive > 0)
        if tr_now.any() and not a.no_critic:
          ret = ret + (g ** (h + 1)) * (alive * tr_now) * critic(o, st["t"]).detach()
        R.append(r.detach()); D.append((term | trunc).float())
        n_term |= term & (alive > 0); n_trunc |= trunc & ~term & (alive > 0)
        alive = alive * (~term & ~trunc).float()
      vH = 0.0 if a.no_critic else critic(o, st["t"])
      loss_a = -(ret + (g ** H) * alive * vH).mean() / H
    if actor_on:
      opt_a.zero_grad(set_to_none=True)
      loss_a.backward()
      gn = torch.nn.utils.clip_grad_norm_(pol.mlp.parameters(), a.clip)
      opt_a.step()
    # critic: TD(lambda) targets on the detached rollout
    with torch.no_grad():
      Ob, Tb = torch.stack(O), torch.stack(TT)
      V = torch.stack([critic(Ob[h], Tb[h]) for h in range(H)] + [critic(o.detach(), st["t"])])
      tgt = torch.zeros(H, N, device=dev)
      nxt = V[H]
      for h in reversed(range(H)):
        nd = 1 - torch.stack(D)[h]
        nxt = R[h] + g * nd * ((1 - lam) * V[h + 1] + lam * nxt)
        tgt[h] = nxt
      m = torch.stack(A) > 0
    xs, ts, ys = Ob[m], Tb[m], tgt[m]
    lc = torch.zeros(())
    for _ in range(0 if a.no_critic else a.critic_epochs):
      perm = torch.randperm(len(ys), device=dev)
      for i in range(0, len(ys), a.critic_batch):
        j = perm[i:i + a.critic_batch]
        lc = ((critic(xs[j], ts[j]) - ys[j]) ** 2).mean()
        opt_c.zero_grad(set_to_none=True); lc.backward(); opt_c.step()
    # reset envs that terminated / reached the clip end
    dead = alive == 0
    if dead.any():
      fresh = rsi(int(dead.sum()))
      for key in st:
        st[key] = st[key].detach().clone()
        if key == "hist":
          st[key][:, dead] = fresh[key]
        else:
          st[key][dead] = fresh[key]
    mins = (time.time() - t0) / 60
    rec = {"it": it, "min": round(mins, 2), "rew_step": round(torch.stack(R).mean().item() / im.DT, 4),
           "alive_end": round(1 - dead.float().mean().item(), 3), "term": round(n_term.float().mean().item(), 3),
           "trunc": round(n_trunc.float().mean().item(), 3), "critic_loss": round(lc.item(), 6),
           "actor_on": actor_on}
    if actor_on:
      rec["grad_norm"] = round(gn.item(), 3)
    if it % a.probe_every == 0 or it == 1:
      rec["probe_rew_step"] = probe()
    log.append(rec)
    if it % a.log_every == 0:
      print(json.dumps(rec), flush=True)
    if actor_on and mins >= next_export:
      pol.export(out / f"model_wm_{mins:05.1f}min.pt", a.init)
      next_export = mins + a.export_min
  pol.export(out / f"model_wm_{(time.time() - t0) / 60:05.1f}min.pt", a.init)
  (out / "log.json").write_text(json.dumps({"args": vars(a), "log": log}))
  print(json.dumps({"done": True, "iters": it, "min": round((time.time() - t0) / 60, 1),
                    "peak_mem_gb": round(torch.cuda.max_memory_allocated() / 1e9, 2)}), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--spec", required=True)
  ap.add_argument("--wm", required=True)
  ap.add_argument("--init", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--out", required=True)
  ap.add_argument("--envs", type=int, default=1024)
  ap.add_argument("--H", type=int, default=32)
  ap.add_argument("--minutes", type=float, default=30)
  ap.add_argument("--export-min", type=float, default=5)
  ap.add_argument("--warmup", type=int, default=50, help="critic-only iterations first")
  ap.add_argument("--gamma", type=float, default=0.99)
  ap.add_argument("--lam", type=float, default=0.95)
  ap.add_argument("--lr-actor", type=float, default=5e-5)
  ap.add_argument("--lr-critic", type=float, default=5e-4)
  ap.add_argument("--clip", type=float, default=1.0)
  ap.add_argument("--noise", type=float, default=0.0)
  ap.add_argument("--critic-epochs", type=int, default=2)
  ap.add_argument("--critic-batch", type=int, default=4096)
  ap.add_argument("--hand-friction", type=float, default=0.6)
  ap.add_argument("--log-every", type=int, default=10)
  ap.add_argument("--probe-every", type=int, default=10)
  ap.add_argument("--no-critic", action="store_true", help="plain H-step return, no value bootstrap")
  ap.add_argument("--fresh", action="store_true", help="every iteration starts from new reference states (RSI)")
  ap.add_argument("--sgd", action="store_true", help="plain SGD on the clipped gradient instead of Adam")
  ap.add_argument("--seed", type=int, default=0)
  main(ap.parse_args())
