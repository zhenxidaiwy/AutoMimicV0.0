"""Train WatchNet on train-split clips (real + synthetic views); evaluate on unseen performers (real video keypoints).

Usage (unitree_rl_mjlab env, which has torch + scipy):
  python train_watch.py --name v1 [--n_synth 40] [--epochs 40] [--no_aux] [--lead 0]
Writes ~/projects/dance/vla/runs/<name>/{model.pt, metrics.json}
Metrics on held-out performers (real view only = the 'real human video' test):
  joint_mae_rad (future chunk), joint_mae_now (k=0), dance_acc, phase_acc, contact_acc
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from data import TEST_CLIPS, TRAIN_CLIPS, WindowDataset, build_clip  # noqa: E402
from model import WatchNet  # noqa: E402


def evaluate(model, ds, device):
  model.eval()
  dl = torch.utils.data.DataLoader(ds, batch_size=512)
  err, err0, dn, ph, ct, n, nc = 0.0, 0.0, 0, 0, 0, 0, 0
  per_dance = {0: [0, 0], 1: [0, 0]}
  with torch.no_grad():
    for x, y, dance, phase, cont in dl:
      x, y = x.to(device), y.to(device)
      o = model(x)
      e = (o["chunk"][..., :29] - y[..., :29]).abs()
      err += e.mean(dim=(1, 2)).sum().item()
      err0 += e[:, 0].mean(dim=1).sum().item()
      n += len(x)
      if "dance" in o:
        pd = o["dance"].argmax(-1).cpu()
        dn += (pd == dance).sum().item()
        for k in (0, 1):
          m = dance == k
          per_dance[k][0] += (pd[m] == k).sum().item()
          per_dance[k][1] += m.sum().item()
        ph += (o["phase"].argmax(-1).cpu() == phase).sum().item()
        pc = o["contact"].argmax(-1).cpu()
        valid = cont >= 0
        ct += (pc[valid] == cont[valid]).sum().item()
        nc += valid.sum().item()
  r = {"joint_mae_rad": err / n, "joint_mae_now": err0 / n, "n": n}
  if dn or ph:
    r.update(dance_acc=dn / n, phase_acc=ph / n, contact_acc=ct / max(nc, 1),
             dance_acc_sss=per_dance[0][0] / max(per_dance[0][1], 1),
             dance_acc_gxdsm=per_dance[1][0] / max(per_dance[1][1], 1))
  model.train()
  return {k: round(v, 4) if isinstance(v, float) else v for k, v in r.items()}


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--name", required=True)
  ap.add_argument("--n_synth", type=int, default=40)
  ap.add_argument("--epochs", type=int, default=40)
  ap.add_argument("--lead", type=int, default=0, help="robot steps (50 Hz) to anticipate")
  ap.add_argument("--no_aux", action="store_true")
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--W", type=int, default=30, help="input window (human frames); 1 = frame-wise shadowing baseline")
  ap.add_argument("--H", type=int, default=25, help="output chunk (robot steps); 1 = no anticipation")
  a = ap.parse_args()
  torch.manual_seed(a.seed)
  dev = "cuda" if torch.cuda.is_available() else "cpu"
  out = Path.home() / "projects/dance/vla/runs" / a.name
  out.mkdir(parents=True, exist_ok=True)

  train_clips = [build_clip(c, a.n_synth, a.seed) for c in TRAIN_CLIPS]
  test_clips = [build_clip(c, 10, a.seed + 1) for c in TEST_CLIPS]
  kw = dict(W=a.W, H=a.H, lead=a.lead)
  tr = WindowDataset(train_clips, augment=True, seed=a.seed, **kw)
  te_real = WindowDataset(test_clips, views=[0], **kw)          # real video keypoints, unseen performers
  te_syn = WindowDataset(test_clips, views=range(1, 11), **kw)  # synthetic viewpoints, unseen performers
  tr_real = WindowDataset(train_clips, views=[0], **kw)         # fit check on training performers
  print(f"train samples {len(tr)} | test real {len(te_real)} | test synth {len(te_syn)} | device {dev}")

  model = WatchNet(W=a.W, H=a.H, aux=not a.no_aux).to(dev)
  opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
  steps = a.epochs * (len(tr) // 256 + 1)
  sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=steps)
  dl = torch.utils.data.DataLoader(tr, batch_size=256, shuffle=True, num_workers=4, drop_last=True)
  t0, hist = time.time(), []
  for ep in range(a.epochs):
    tot = 0.0
    for x, y, dance, phase, cont in dl:
      x, y = x.to(dev), y.to(dev)
      o = model(x)
      loss = F.smooth_l1_loss(o["chunk"], y, beta=0.05)
      if not a.no_aux:
        loss = loss + 0.2 * F.cross_entropy(o["dance"], dance.to(dev)) \
                    + 0.2 * F.cross_entropy(o["phase"], phase.to(dev)) \
                    + 0.2 * F.cross_entropy(o["contact"].reshape(-1, 2), cont.to(dev).reshape(-1), ignore_index=-1)
      opt.zero_grad()
      loss.backward()
      torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
      opt.step()
      sched.step()
      tot += loss.item()
    if ep % 5 == 4 or ep == a.epochs - 1:
      m = evaluate(model, te_real, dev)
      hist.append({"epoch": ep + 1, "loss": tot / len(dl), "test_real": m})
      print(f"ep {ep + 1:3d} loss {tot / len(dl):.4f} | unseen-performer real video: {m} | {time.time() - t0:.0f}s",
            flush=True)
  res = {"args": vars(a), "test_real": evaluate(model, te_real, dev), "test_synth_views": evaluate(model, te_syn, dev),
         "train_real": evaluate(model, tr_real, dev), "history": hist}
  torch.save({"model": model.state_dict(), "args": vars(a)}, out / "model.pt")
  json.dump(res, open(out / "metrics.json", "w"), indent=1)
  print("FINAL", json.dumps({k: v for k, v in res.items() if k != "history"}))
