"""Same spread statistics for several timelines: reference vs robot lateral ankle distance (median / p90 / max)."""
import sys
from pathlib import Path

import numpy as np

O = Path.home() / "projects/dance_logs/follow_analysis"
for name in sys.argv[1:]:
  R = np.load(O / f"{name}.npz")["rec"]
  k = R[:, 0] > 1.0
  ref, rob = np.abs(R[k, 6]), np.abs(R[k, 4])
  print(f"{name:<16} reference median {np.median(ref):.2f} p90 {np.percentile(ref, 90):.2f} max {ref.max():.2f} | "
        f"robot median {np.median(rob):.2f} p90 {np.percentile(rob, 90):.2f} max {rob.max():.2f}  "
        f"| robot p90 / reference p90 = {np.percentile(rob, 90) / np.percentile(ref, 90):.0%}")
