"""Aggregate closed-loop results: per mode (oracle / v1_aux / lead5 / shadow) over clips and seeds."""
import glob
import json
import os
import re
from collections import defaultdict

import numpy as np

if __name__ == "__main__":
  D = os.path.expanduser("~/projects/dance/vla/closed_loop")
  rows = defaultdict(list)
  for p in glob.glob(f"{D}/*.json"):
    r = json.load(open(p))["result"]
    mode = "oracle" if r["mode"] == "oracle" else re.sub(r"_s\d+$", "", r["watch"])
    if r["watch"] == "smoke" and r["mode"] != "oracle":
      continue
    rows[(mode, r["clip"])].append(r)
  modes = ["oracle", "v1_aux", "lead5", "shadow"]
  clips = sorted({c for _, c in rows})
  print(f"{'mode':<8} {'clip':<18} {'n':>2} {'completed':>9} {'fell_at_s(mean)':>15} {'joint_err':>10} {'body_err':>9} {'pred_sss':>8}")
  for m in modes:
    allr = []
    for c in clips:
      rs = rows.get((m, c), [])
      if not rs:
        continue
      allr += rs
      done = np.mean([r["completed"] for r in rs])
      fell = [r["fell_at_s"] for r in rs if r["fell_at_s"] is not None]
      ps = [r["dance_pred_frac_sss"] for r in rs if r["dance_pred_frac_sss"] is not None]
      print(f"{m:<8} {c:<18} {len(rs):>2} {done:>9.2f} {np.mean(fell) if fell else float('nan'):>15.2f} "
            f"{np.mean([r['joint_err_vs_gt_mean'] for r in rs]):>10.3f} {np.mean([r['body_pos_err_vs_gt_mean'] for r in rs]):>9.3f} "
            f"{np.mean(ps) if ps else float('nan'):>8.2f}")
    if allr:
      print(f"{m:<8} {'ALL':<18} {len(allr):>2} {np.mean([r['completed'] for r in allr]):>9.2f}")
