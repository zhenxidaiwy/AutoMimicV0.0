"""Open-set skill retrieval: RetrieveNet with one extra "other" class (index NC) so motions that are neither learned
dance are rejected instead of being forced into the closest dance state (the closed-set model triggered on 8/9
negative test videos).

Negatives ("other") come only from AIST++ 3D keypoints (COCO-17, 60 fps; annotations CC BY 4.0, Google LLC; 10 street
dance genres) projected to 2D with the same random cameras as the synthetic training views (data.synth_views), plus
standing-still / swaying windows made from them. The live negative test videos are NEVER used for training.
Usage (unitree_rl_mjlab env): python train_retrieve_open.py --name open_s0 [--neg_frac 0.35] [--epochs 40]
"""
import argparse
import json
import pickle
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn.functional as F

from data import normalise, synth_views
from train_retrieve import NC, SOFT, STATE_DANCE, TEST_CLIPS, TRAIN_CLIPS, RetrieveDS, RetrieveNet, prepare

AIST = Path.home() / "projects/dance/data/aistpp"
KPDIR = Path.home() / "projects/dance/vla/kp"
K_TRAIN = np.array([[1200.0, 0, 480], [0, 1200.0, 360], [0, 0, 1]])
WH = np.array([960.0, 720.0])


def load_aist(max_seq, seed):
  """AIST++ sequences -> camera-style joints (m, y down, person ~4.5 m in front), 30 fps."""
  ign = set()
  if (AIST / "ignore_list.txt").exists():
    ign = {l.strip() for l in open(AIST / "ignore_list.txt") if l.strip()}
  files = sorted(p for p in (AIST / "keypoints3d").glob("*.pkl") if p.stem not in ign)
  rng = np.random.default_rng(seed)
  rng.shuffle(files)
  out = []
  for p in files[:max_seq]:
    d = pickle.load(open(p, "rb"))
    j = np.asarray(d.get("keypoints3d_optim", d.get("keypoints3d")), np.float64)[::2]  # 60 -> 30 fps
    if len(j) < 40 or not np.isfinite(j).all():
      continue
    up = (j[:, 0] - (j[:, 15] + j[:, 16]) / 2).mean(0)
    h = np.linalg.norm(up)
    j = j / (100.0 if h > 10 else 1.0)  # cm -> m
    up = up / h
    # world -> camera: y_cam = -up; x_cam perpendicular, z forward (random facing is added by synth_views' yaw)
    fwd = np.cross(up, [1.0, 0, 0]) if abs(up[0]) < 0.9 else np.cross(up, [0, 0, 1.0])
    fwd /= np.linalg.norm(fwd)
    x = np.cross(-up, fwd)
    R = np.stack([x, -up, fwd])
    jc = (j - j[:, [11, 12]].mean((0, 1))) @ R.T
    jc[..., 2] += 4.5
    out.append(jc)
  return out


class NegDS(torch.utils.data.Dataset):
  """Random 1 s windows of AIST++ sequences seen from random cameras, label NC ("other")."""

  def __init__(self, seqs, n, W=30, seed=0, fixed=False):
    self.s, self.n, self.W, self.seed, self.fixed = seqs, n, W, seed, fixed

  def __len__(self):
    return self.n

  def __getitem__(self, i):
    # fixed: the same window for index i every time (validation); else fresh randomness (also per DataLoader worker)
    r = np.random.default_rng([self.seed, i]) if self.fixed else np.random.default_rng()
    s = self.s[r.integers(len(self.s))]
    speed = r.uniform(0.6, 1.6)  # tempo augmentation
    t0 = r.uniform(0, max(1.0, len(s) - self.W * speed - 1))
    idx = np.clip(np.round(t0 + np.arange(self.W) * speed).astype(int), 0, len(s) - 1)
    seg = s[idx]
    if r.random() < 0.15:  # near-still: hold one pose with small sway (standing / talking)
      seg = np.repeat(seg[:1], self.W, 0) + r.normal(0, 0.01, (self.W, 17, 3)).cumsum(0) * 0.3
    win = synth_views(seg, K_TRAIN, WH, 1, r)[0].astype(np.float32)
    tor = np.median(np.linalg.norm((win[:, 5, :2] + win[:, 6, :2]) / 2 - (win[:, 11, :2] + win[:, 12, :2]) / 2, axis=-1))
    win[..., :2] += r.normal(0, 0.03 * tor, win[..., :2].shape)
    # confidence stays 1 like the synthetic positive views (U(0.6, 1) here was a shortcut: open_s0 learned
    # "imperfect confidence -> other" and rejected real positives); ConfAug randomises both classes alike
    drop = r.random(win.shape[:2]) < 0.05
    drop[:, [5, 6, 11, 12]] = False
    win[drop, 2] = 0
    win[drop, :2] = 0
    return torch.from_numpy(normalise(win).reshape(self.W, -1)), torch.tensor(NC), torch.tensor(-1)


class RealNegDS(torch.utils.data.Dataset):
  """Random 1 s windows of real YOLO keypoints (live_tests negatives batch 1, kp_live_tests.py), label NC.
  Batch 2 (neg_10..) stays held out for testing."""

  def __init__(self, names, n, W=30, kdir="kp_live"):
    self.k = []
    for nm in names:
      z = np.load(Path.home() / "projects/dance/vla" / kdir / f"{nm}.npz")
      self.k.append(z["kp"][z["sent"]].astype(np.float32))
    self.n, self.W = n, W

  def __len__(self):
    return self.n

  def __getitem__(self, i):
    r = np.random.default_rng()
    k = self.k[r.integers(len(self.k))]
    speed = r.uniform(0.8, 1.25)
    t0 = r.uniform(0, max(1.0, len(k) - self.W * speed - 1))
    win = k[np.clip(np.round(t0 + np.arange(self.W) * speed).astype(int), 0, len(k) - 1)].copy()
    if r.random() < 0.5:  # mirror
      win[..., 0] = -win[..., 0]
      win = win[:, [0, 2, 1, 4, 3, 6, 5, 8, 7, 10, 9, 12, 11, 14, 13, 16, 15]]
    tor = np.median(np.linalg.norm((win[:, 5, :2] + win[:, 6, :2]) / 2 - (win[:, 11, :2] + win[:, 12, :2]) / 2, axis=-1))
    win[..., :2] += r.normal(0, 0.03 * tor, win[..., :2].shape)
    return torch.from_numpy(normalise(win).reshape(self.W, -1)), torch.tensor(NC), torch.tensor(-1)


POS_ANY = -2  # label: "doing one of the learned dances", canonical frame unknown (loss = -log P(not other))


class PosAnyDS(RealNegDS):
  """Random 1 s windows of real YOLO keypoints of extra dance performers (data/pos_train via kp_live_tests.py
  --dir), labelled POS_ANY: they only teach the veto that these people are dancing."""

  def __getitem__(self, i):
    x, _, h = super().__getitem__(i)
    return x, torch.tensor(POS_ANY), h


class ConfAug(torch.utils.data.Dataset):
  """With probability p replace the confidence of the visible joints by U(0.4, 1) (positives and negatives alike), so
  the confidence channel carries no class information."""

  def __init__(self, ds, p=0.5):
    self.ds, self.p = ds, p

  def __len__(self):
    return len(self.ds)

  def __getitem__(self, i):
    x, y, h = self.ds[i]
    r = np.random.default_rng()
    if r.random() < self.p:
      x = x.clone()
      c = x[:, 2::3]
      vis = c > 0
      c[vis] = torch.from_numpy(r.uniform(0.4, 1.0, int(vis.sum())).astype(np.float32))
      x[:, 2::3] = c
    return x, y, h


class OpenNet(RetrieveNet):
  def __init__(self):
    super().__init__()
    d2 = self.head[-1].in_features
    self.head[-1] = torch.nn.Linear(d2, NC + 1)


def evaluate(model, ds, dev, other_thr=0.5):
  model.eval()
  P, Y = [], []
  with torch.no_grad():
    for x, y, _ in torch.utils.data.DataLoader(ds, batch_size=512):
      P.append(model(x.to(dev)).softmax(-1).cpu().numpy())
      Y.append(y.numpy())
  model.train()
  p, y = np.concatenate(P), np.concatenate(Y)
  other = p[:, NC] >= other_thr
  dance_pred = np.array([int(p[i, :NC][STATE_DANCE == 1].sum() > p[i, :NC][STATE_DANCE == 0].sum()) for i in range(len(p))])
  pos = y < NC
  res = {"n": int(len(y))}
  if pos.any():
    res["pos_rejected"] = round(float(other[pos].mean()), 4)
    res["dance_acc"] = round(float((dance_pred[pos] == STATE_DANCE[y[pos]]).mean()), 4)
  if (~pos).any():
    res["neg_rejected"] = round(float(other[~pos].mean()), 4)
  return res


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--name", required=True)
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--epochs", type=int, default=40)
  ap.add_argument("--n_synth", type=int, default=40)
  ap.add_argument("--neg_frac", type=float, default=0.35, help="fraction of 'other' windows in each epoch")
  ap.add_argument("--max_seq", type=int, default=1200)
  ap.add_argument("--conf_aug", type=float, default=0.5, help="probability of randomising the confidence channel")
  ap.add_argument("--yolo_views", type=int, default=0, help="copies of each training clip's real YOLO view to add")
  ap.add_argument("--real_neg", default="", help="comma list of kp_live videos used as real 'other' windows")
  ap.add_argument("--real_neg_frac", type=float, default=0.3, help="real negative windows relative to AIST++ ones")
  ap.add_argument("--pos_any", type=float, default=0.0,
                  help="extra-dancer windows (kp_pos/*.npz, label POS_ANY) relative to the positive training windows")
  a = ap.parse_args()
  torch.manual_seed(a.seed)
  dev = "cuda" if torch.cuda.is_available() else "cpu"
  out = Path.home() / "projects/dance/vla/runs" / a.name
  out.mkdir(parents=True, exist_ok=True)
  seqs = load_aist(a.max_seq, a.seed)
  n_val = max(20, len(seqs) // 10)  # held-out AIST++ sequences for the negative validation set
  print(f"AIST++ sequences: {len(seqs)} ({n_val} held out)", flush=True)
  tr_c, te_c = prepare(TRAIN_CLIPS, a.n_synth, a.seed), prepare(TEST_CLIPS, 0, a.seed)
  if a.yolo_views:
    # real YOLO keypoints of the TRAINING clips as extra positive views (live detector noise is not "other")
    for c in tr_c:
      f = KPDIR / f"{c['id']}_yolo.npz"
      if f.exists():
        yk = np.load(f)["kp2d_real"].astype(np.float32)
        T = min(len(yk), c["kp"].shape[1])
        c["kp"] = np.concatenate([c["kp"][:, :T]] + [yk[None, :T]] * a.yolo_views, 0)
        c["cls"] = c["cls"][:T]
    print("yolo views added:", sum((KPDIR / f"{c['id']}_yolo.npz").exists() for c in tr_c), "clips", flush=True)
  tr_pos = RetrieveDS(tr_c, augment=True, seed=a.seed)
  n_neg = int(len(tr_pos) * a.neg_frac / (1 - a.neg_frac))
  parts = [tr_pos, NegDS(seqs[n_val:], n_neg, seed=a.seed)]
  if a.real_neg:
    parts.append(RealNegDS(a.real_neg.split(","), int(n_neg * a.real_neg_frac)))
    print(f"real negatives: {a.real_neg} ({len(parts[-1])} windows / epoch)", flush=True)
  if a.pos_any:
    names = sorted(p.stem for p in (Path.home() / "projects/dance/vla/kp_pos").glob("*.npz"))
    parts.append(PosAnyDS(names, int(len(tr_pos) * a.pos_any), kdir="kp_pos"))
    print(f"extra dancers (POS_ANY): {len(names)} clips ({len(parts[-1])} windows / epoch)", flush=True)
  tr = torch.utils.data.ConcatDataset(parts)
  if a.conf_aug > 0:
    tr = ConfAug(tr, a.conf_aug)
  te = RetrieveDS(te_c, views=[0])
  neg_val = NegDS(seqs[:n_val], 4000, seed=a.seed + 99, fixed=True)
  soft = np.zeros((NC + 1, NC + 1), np.float32)
  soft[:NC, :NC] = SOFT
  soft[NC, NC] = 1.0
  soft = torch.tensor(soft, device=dev)
  model = OpenNet().to(dev)
  opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-2)
  dl = torch.utils.data.DataLoader(tr, batch_size=256, shuffle=True, num_workers=4, drop_last=True)
  sched = torch.optim.lr_scheduler.OneCycleLR(opt, max_lr=1e-3, total_steps=a.epochs * len(dl))
  t0 = time.time()
  for ep in range(a.epochs):
    tot = 0.0
    for x, y, _ in dl:
      y = y.to(dev)
      lsm = F.log_softmax(model(x.to(dev)), -1)
      anyp = y == POS_ANY
      per = -(soft[y.clamp(min=0)] * lsm).sum(-1)
      per = torch.where(anyp, -torch.logsumexp(lsm[:, :NC], -1), per)  # POS_ANY: -log P(not other)
      loss = per.mean()
      opt.zero_grad()
      loss.backward()
      opt.step()
      sched.step()
      tot += loss.item()
    if ep % 10 == 9 or ep == a.epochs - 1:
      print(f"ep {ep + 1} loss {tot / len(dl):.3f} | unseen dancers: {evaluate(model, te, dev)} | "
            f"held-out AIST++: {evaluate(model, neg_val, dev)} | {time.time() - t0:.0f}s", flush=True)
  res = {"args": vars(a), "test_real": evaluate(model, te, dev), "neg_val": evaluate(model, neg_val, dev)}
  torch.save({"model": model.state_dict(), "args": vars(a), "n_classes": NC + 1, "open": True}, out / "model.pt")
  json.dump(res, open(out / "metrics.json", "w"), indent=1)
  print("FINAL", json.dumps(res))
