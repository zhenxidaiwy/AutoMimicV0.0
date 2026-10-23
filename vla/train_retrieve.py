"""Skill-retrieval high level: human keypoint window -> canonical skill state (which canonical frame to play now).

Targets come from align.py (VLM phase/swing labels align every performer to the canonical clip of their dance).
Soft labels: a Gaussian over canonical frames of the same dance (sigma 1.5 frames) so neighbouring frames are near-misses.
Usage (unitree_rl_mjlab env): python train_retrieve.py --name r1 [--seed 0] [--lead 0] [--epochs 40] [--n_synth 40]
Metrics on unseen performers (real video): state_acc (exact), frame_err (|canonical frame error| in 30 fps frames,
same-dance predictions), segment_acc (predicted canonical phase name == canonical phase of the aligned target),
human_phase_acc (predicted canonical phase name == the human's own VLM phase label), dance_acc.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

sys.path.insert(0, str(Path(__file__).resolve().parent))
from align import CANON, DS, align, state_table, to_class  # noqa: E402
from data import TEST_CLIPS, TRAIN_CLIPS, build_clip, normalise  # noqa: E402

TABLE = state_table()
NC = len(TABLE)
CANON_PHASE = {m: json.load(open(DS / c / "annotation.json", encoding="utf-8"))["phase"] for m, c in CANON.items()}
STATE_PHASE = [CANON_PHASE[m][int(f)] for m, f in TABLE]
STATE_DANCE = np.array([0 if m == "闪身步" else 1 for m, _ in TABLE])
STATE_FRAME = np.array([f for _, f in TABLE], float)
# soft-label matrix: row = target class, Gaussian over same-dance canonical frames
SOFT = np.zeros((NC, NC), np.float32)
for i in range(NC):
  same = STATE_DANCE == STATE_DANCE[i]
  w = np.exp(-0.5 * ((STATE_FRAME - STATE_FRAME[i]) / 1.5) ** 2) * same
  SOFT[i] = w / w.sum()


class RetrieveDS(torch.utils.data.Dataset):
  def __init__(self, clips, W=30, lead=0, augment=False, views=None, seed=0):
    self.c, self.W, self.lead, self.aug = clips, W, lead, augment
    self.rng = np.random.default_rng(seed)
    self.index = [(ci, v, t) for ci, c in enumerate(clips)
                  for v in (range(c["kp"].shape[0]) if views is None else views) for t in range(c["kp"].shape[1])]

  def __len__(self):
    return len(self.index)

  def __getitem__(self, i):
    ci, v, t = self.index[i]
    c = self.c[ci]
    T = c["kp"].shape[1]
    win = c["kp"][v, np.clip(np.arange(t - self.W + 1, t + 1), 0, T - 1)].copy()
    if self.aug:
      r = self.rng
      tor = np.median(np.linalg.norm((win[:, 5, :2] + win[:, 6, :2]) / 2 - (win[:, 11, :2] + win[:, 12, :2]) / 2, axis=-1))
      win[..., :2] += r.normal(0, 0.03 * tor, win[..., :2].shape)
      drop = r.random(win.shape[:2]) < 0.05
      drop[:, [5, 6, 11, 12]] = False
      win[drop, 2] = 0
      win[drop, :2] = 0
    tt = min(t + self.lead, T - 1)
    return (torch.from_numpy(normalise(win).reshape(self.W, -1)), torch.tensor(c["cls"][tt]),
            torch.tensor(c["phase"][tt]))


class RetrieveNet(nn.Module):
  def __init__(self, W=30, d=128, layers=3, heads=4):
    super().__init__()
    self.inp = nn.Linear(51, d)
    self.pos = nn.Parameter(torch.zeros(1, W, d))
    self.enc = nn.TransformerEncoder(nn.TransformerEncoderLayer(d, heads, 4 * d, 0.1, batch_first=True, norm_first=True), layers)
    self.norm = nn.LayerNorm(2 * d)
    self.head = nn.Sequential(nn.Linear(2 * d, 2 * d), nn.GELU(), nn.Linear(2 * d, NC))

  def forward(self, x):
    h = self.enc(self.inp(x) + self.pos)
    return self.head(self.norm(torch.cat([h[:, -1], h.mean(1)], -1)))


def prepare(cids, n_synth, seed):
  out = []
  for cid in cids:
    c = build_clip(cid, n_synth, seed)
    canon, move = align(cid)
    c["cls"] = to_class(canon, move, TABLE)[: c["kp"].shape[1]]
    out.append(c)
  return out


def evaluate(model, ds, dev):
  from data import PHASES
  model.eval()
  P, Y, H = [], [], []
  with torch.no_grad():
    for x, y, hp in torch.utils.data.DataLoader(ds, batch_size=512):
      P.append(model(x.to(dev)).argmax(-1).cpu().numpy())
      Y.append(y.numpy())
      H.append(hp.numpy())
  model.train()
  p, y, hp = map(np.concatenate, (P, Y, H))
  same = STATE_DANCE[p] == STATE_DANCE[y]
  return {"state_acc": round(float((p == y).mean()), 4),
          "frame_err": round(float(np.abs(STATE_FRAME[p] - STATE_FRAME[y])[same].mean()), 2),
          "segment_acc": round(float(np.mean([STATE_PHASE[a] == STATE_PHASE[b] for a, b in zip(p, y)])), 4),
          "human_phase_acc": round(float(np.mean([STATE_PHASE[a] == PHASES[h] for a, h in zip(p, hp)])), 4),
          "dance_acc": round(float(same.mean()), 4), "n": int(len(p))}


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--name", required=True)
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--lead", type=int, default=0, help="human frames (30 fps) to anticipate")
  ap.add_argument("--epochs", type=int, default=40)
  ap.add_argument("--n_synth", type=int, default=40)
  a = ap.parse_args()
  torch.manual_seed(a.seed)
  dev = "cuda" if torch.cuda.is_available() else "cpu"
  out = Path.home() / "projects/dance/vla/runs" / a.name
  out.mkdir(parents=True, exist_ok=True)
  tr_c, te_c = prepare(TRAIN_CLIPS, a.n_synth, a.seed), prepare(TEST_CLIPS, 0, a.seed)
  tr = RetrieveDS(tr_c, lead=a.lead, augment=True, seed=a.seed)
  te = RetrieveDS(te_c, lead=a.lead, views=[0])
  soft = torch.tensor(SOFT, device=dev)
  model = RetrieveNet().to(dev)
  opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
  dl = torch.utils.data.DataLoader(tr, batch_size=256, shuffle=True, num_workers=4, drop_last=True)
  sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=a.epochs * len(dl))
  t0 = time.time()
  for ep in range(a.epochs):
    tot = 0.0
    for x, y, _ in dl:
      logits = model(x.to(dev))
      loss = -(soft[y.to(dev)] * F.log_softmax(logits, -1)).sum(-1).mean()
      opt.zero_grad()
      loss.backward()
      opt.step()
      sched.step()
      tot += loss.item()
    if ep % 10 == 9 or ep == a.epochs - 1:
      print(f"ep {ep + 1} loss {tot / len(dl):.3f} | unseen real: {evaluate(model, te, dev)} | {time.time() - t0:.0f}s", flush=True)
  res = {"args": vars(a), "test_real": evaluate(model, te, dev),
         "train_real": evaluate(model, RetrieveDS(tr_c, lead=a.lead, views=[0]), dev)}
  torch.save({"model": model.state_dict(), "args": vars(a), "n_classes": NC}, out / "model.pt")
  json.dump(res, open(out / "metrics.json", "w"), indent=1)
  print("FINAL", json.dumps(res))
