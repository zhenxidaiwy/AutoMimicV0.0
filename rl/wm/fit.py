"""Fit the G1 world model on collected files (SuperMimic recipe: k-step autoregressive windows on logged actions,
Adam, global grad-norm clip 1.0), then evaluate 32-step open-loop rollouts on held-out files.
Usage: python fit.py --data <dir with *.npz> --out <dir> [--holdout cartwheel_2_r11,...] [--iters 50000]
  [--hidden 1024,1024,1024] [--k 8] [--batch 2048] [--eval-only <model.pt>]"""
import argparse
import json
import time
from pathlib import Path

import torch

import wm


def loss_fn(model, b, k):
  s0, a, xi = b["s"][:, 0], b["a"], b["xi"]
  S, R = model.rollout(s0, a[:, :k], xi)
  ls = ((model.ns(S[:, 1:]) - model.ns(b["s"][:, 1:k + 1])) ** 2).mean()
  lr = ((model.nroot(R) - model.nroot(b["droot"][:, :k])) ** 2).mean()
  lb = ((model.nbody(model.body(b["s"])) - model.nbody(b["body"])) ** 2).mean()  # the head on true states
  return ls + lr + lb, {"state": ls.item(), "root": lr.item(), "body": lb.item()}


@torch.no_grad()
def evaluate(model, data, H):
  """open loop over H steps on logged actions: errors in physical units at step H (and mean over the window)."""
  s0, a, xi = data["s"][:, 0], data["a"][:, :H], data["xi"]
  S, R = model.rollout(s0, a, xi)
  true = data["s"][:, : H + 1]
  e_h = (S[..., 0] - true[..., 0]).abs()
  e_j = (S[..., 13:13 + wm.NJ] - true[..., 13:13 + wm.NJ]).abs().mean(-1)
  Rp, Rt = wm.six_to_mat(S[..., 1:7]), wm.six_to_mat(true[..., 1:7])
  e_tilt = torch.rad2deg(torch.arccos(((Rp.transpose(-1, -2) @ Rt).diagonal(dim1=-2, dim2=-1).sum(-1) - 1)
                                      .div(2).clamp(-1, 1)))
  bp, bt = model.body(S).unflatten(-1, (-1, 3)), data["body"][:, : H + 1].unflatten(-1, (-1, 3))
  e_b = (bp - bt).norm(dim=-1).mean(-1)
  # root xy drift: integrate the predicted heading-frame steps
  def integrate(dr):
    yaw = torch.cumsum(dr[..., 0], 1)
    yaw_prev = torch.cat([torch.zeros_like(yaw[:, :1]), yaw[:, :-1]], 1)
    c, s = torch.cos(yaw_prev), torch.sin(yaw_prev)
    return torch.stack([torch.cumsum(c * dr[..., 1] - s * dr[..., 2], 1), torch.cumsum(s * dr[..., 1] + c * dr[..., 2], 1)], -1)
  e_xy = (integrate(R) - integrate(data["droot"][:, :H])).norm(dim=-1)
  q = lambda x: {"end": round(x[:, -1].mean().item(), 4), "p90_end": round(x[:, -1].quantile(0.9).item(), 4)}
  return {"H": H, "windows": int(s0.shape[0]), "root_height_m": q(e_h), "joint_pos_rad": q(e_j),
          "tilt_deg": q(e_tilt), "body_pos_m": q(e_b), "root_xy_m": q(e_xy)}


def main(a):
  dev = "cuda" if torch.cuda.is_available() and not a.cpu else "cpu"
  files = sorted(Path(a.data).glob("*.npz"))
  hold = [f for f in files if any(h in f.name for h in a.holdout.split(",") if h)]
  train = [f for f in files if f not in hold]
  out = Path(a.out)
  out.mkdir(parents=True, exist_ok=True)
  hidden = tuple(int(x) for x in a.hidden.split(","))
  if a.eval_only:
    model, meta = wm.load(a.eval_only, dev)
  else:
    data = wm.Sequences(train, a.k, dev)
    if a.env_stride > 1:  # data-scaling test: keep every n-th env trajectory of every file (same checkpoint coverage)
      data.starts = data.starts[(data.starts // a.steps_per_env) % a.env_stride == 0]
    print(json.dumps({"train_files": len(train), "holdout_files": len(hold), "windows": len(data),
                      "transitions": int(data.s.shape[0])}), flush=True)
    model = wm.WorldModel(data.body.shape[-1], hidden).to(dev)
    model.fit_norms(data.stats_sample())
    opt = torch.optim.Adam(model.parameters(), lr=a.lr)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, a.iters, eta_min=a.lr * 0.03)
    gen = torch.Generator(device=dev).manual_seed(0)
    t0 = time.time()
    for it in range(1, a.iters + 1):
      loss, parts = loss_fn(model, data.sample(a.batch, gen), a.k)
      opt.zero_grad(set_to_none=True)
      loss.backward()
      torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
      opt.step()
      sched.step()
      if it % a.log_every == 0 or it == a.iters:
        print(json.dumps({"it": it, "loss": round(loss.item(), 5), **{k: round(v, 5) for k, v in parts.items()},
                          "min": round((time.time() - t0) / 60, 1)}), flush=True)
      if it % a.save_every == 0 or it == a.iters:
        wm.save(model, out / "wm.pt", {"hidden": list(hidden), "k": a.k, "iters": it, "train": [f.name for f in train]})
    del data
  model.eval()
  res = {}
  for name, fs in (("train_sample", train[:3]), ("holdout", hold)):
    if not fs:
      continue
    seq = wm.Sequences(fs, a.horizon, dev)
    sel = torch.randperm(len(seq), device=dev, generator=torch.Generator(device=dev).manual_seed(1))[: a.eval_windows]
    ev = seq.windows(sel)
    del seq
    res[name] = {f"H{h}": evaluate(model, ev, h) for h in (8, a.horizon)}
    del ev
  # P2 gate "including the hand-support phase": held-out cartwheel windows starting in the support phase
  cw = [f for f in hold if "cw2auto" in f.name]
  if cw and a.support_frames:
    lo, hi = (int(x) for x in a.support_frames.split(","))
    seq = wm.Sequences(cw, a.horizon, dev)
    fr = seq.frame[seq.starts]
    idx = torch.nonzero((fr >= lo) & (fr <= hi)).squeeze(1)[: a.eval_windows]
    if len(idx):
      res["holdout_cartwheel_support"] = {"frames": [lo, hi], **{f"H{h}": evaluate(model, seq.windows(idx), h)
                                                                for h in (8, a.horizon)}}
    del seq
  (out / "eval.json").write_text(json.dumps(res, indent=1))
  print(json.dumps(res), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--data", required=True)
  ap.add_argument("--out", required=True)
  ap.add_argument("--holdout", default="")
  ap.add_argument("--iters", type=int, default=50000)
  ap.add_argument("--hidden", default="1024,1024,1024")
  ap.add_argument("--k", type=int, default=8)
  ap.add_argument("--batch", type=int, default=2048)
  ap.add_argument("--lr", type=float, default=2e-4)
  ap.add_argument("--horizon", type=int, default=32)
  ap.add_argument("--eval-windows", type=int, default=20000)
  ap.add_argument("--log-every", type=int, default=500)
  ap.add_argument("--save-every", type=int, default=5000)
  ap.add_argument("--eval-only", default="")
  ap.add_argument("--support-frames", default="46,80", help="cartwheel_2 support phase (labels: support 46-80)")
  ap.add_argument("--env-stride", type=int, default=1, help="keep 1/n of the env trajectories (data-scaling test)")
  ap.add_argument("--steps-per-env", type=int, default=200, help="T of the collected files (env id = row // T)")
  ap.add_argument("--cpu", action="store_true")
  main(ap.parse_args())
