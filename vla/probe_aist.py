"""Sanity check of the AIST++ -> camera-frame conversion used by train_retrieve_open.load_aist."""
import pickle
from pathlib import Path

import numpy as np

from train_retrieve_open import AIST, K_TRAIN, WH, NegDS, load_aist
from data import synth_views

p = sorted((AIST / "keypoints3d").glob("*.pkl"))[0]
d = pickle.load(open(p, "rb"))
print(p.name, {k: np.shape(v) for k, v in d.items()})
seqs = load_aist(30, 0)
print("sequences", len(seqs), "frames", [len(s) for s in seqs[:5]])
s = seqs[0]
print("nose", s[:, 0].mean(0).round(2), "mid-hip", s[:, [11, 12]].mean((0, 1)).round(2),
      "mid-ankle", s[:, [15, 16]].mean((0, 1)).round(2),
      "height", np.linalg.norm(s[:, 0] - s[:, [15, 16]].mean(1), axis=-1).mean().round(2))
uv = synth_views(s[:30], K_TRAIN, WH, 1, np.random.default_rng(0))[0]
print("2D nose y", uv[:, 0, 1].mean().round(1), "ankle y", uv[:, 15, 1].mean().round(1), "(y down: nose < ankle)")
x, y, _ = NegDS(seqs, 10, fixed=True)[0]
print("window", tuple(x.shape), "label", int(y))
