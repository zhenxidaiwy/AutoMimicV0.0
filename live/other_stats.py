"""Distribution of the open-set 'other' probability per test video (from trigger_eval ticks.json)."""
import json
import sys
from pathlib import Path

import numpy as np

t = json.load(open(Path.home() / "projects/dance/vla/trigger_eval" / sys.argv[1] / "ticks.json"))
for n, ticks in sorted(t.items()):
  o = np.array([x["other"] for x in ticks if x["vis"] == "ok"])
  if len(o):
    print(f"{n:<18} ticks {len(o):>3}  other median {np.median(o):.3f}  p90 {np.percentile(o, 90):.3f}  "
          f"frac>0.5 {np.mean(o > 0.5):.2f}")
