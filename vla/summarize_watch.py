"""Aggregate high-level model runs (mean ± std over seeds) for real-video unseen-performer test and synthetic views."""
import glob
import json
import os
import re
from collections import defaultdict

import numpy as np

if __name__ == "__main__":
  R = os.path.expanduser("~/projects/dance/vla/runs")
  groups = defaultdict(list)
  for p in sorted(glob.glob(f"{R}/*/metrics.json")):
    name = os.path.basename(os.path.dirname(p))
    if not re.search(r"_s\d+$", name):
      continue
    groups[re.sub(r"_s\d+$", "", name)].append(json.load(open(p)))
  keys = ["joint_mae_rad", "joint_mae_now", "dance_acc", "dance_acc_sss", "dance_acc_gxdsm", "phase_acc", "contact_acc"]
  for split in ("test_real", "test_synth_views", "train_real"):
    print(f"\n== {split}")
    print(f"{'group':<14}" + "".join(f"{k:>18}" for k in keys))
    for g, runs in groups.items():
      row = f"{g:<14}"
      for k in keys:
        v = [r[split][k] for r in runs if k in r[split]]
        row += f"{np.mean(v):>11.3f}±{np.std(v):.3f}" if v else f"{'-':>18}"
      print(row + f"   (n={len(runs)})")
