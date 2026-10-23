"""Ground-heavy start-state prior for the backflip probe: most episodes start on the ground so the robot must earn
the flight itself (starting in the air gave flight rewards for free). Phase weights below -> per-frame rsi_weight.
Usage (any env with numpy): python flip_prior.py backflip_3 ...   -> dataset/<clip>/flip_prior_50fps.npz
"""
import sys
from pathlib import Path

import numpy as np

W = {"stand": 0.4, "crouch": 2.0, "takeoff": 2.0, "flight": 0.3, "land": 1.0, "settle": 0.5, "other": 0.5}
for cid in sys.argv[1:]:
  d = Path.home() / "projects/dance/dataset" / cid
  z = np.load(d / "labels_50fps.npz")
  names = [str(x) for x in z["phase_names"]]
  w = np.array([W[names[p]] for p in z["phase"]], np.float64)
  w /= w.sum()
  np.savez(d / "flip_prior_50fps.npz", rsi_weight=w, phase=z["phase"], phase_names=z["phase_names"])
  share = {n: round(float(w[z["phase"] == i].sum()), 3) for i, n in enumerate(names) if (z["phase"] == i).any()}
  print(cid, "start-state share per phase:", share)
