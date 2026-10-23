"""Mean ± std over seeds for retrieval models (unseen performers, real video)."""
import glob
import json
import os
import re
from collections import defaultdict

import numpy as np

if __name__ == "__main__":
  R = os.path.expanduser("~/projects/dance/vla/runs")
  g = defaultdict(list)
  for p in glob.glob(f"{R}/ret_lead*_s*/metrics.json"):
    g[re.sub(r"_s\d+$", "", os.path.basename(os.path.dirname(p)))].append(json.load(open(p)))
  keys = ["state_acc", "frame_err", "segment_acc", "human_phase_acc", "dance_acc"]
  for split in ("test_real", "train_real"):
    print(f"== {split}")
    for name, runs in sorted(g.items()):
      print(f"{name:<10}" + "".join(f"  {k} {np.mean([r[split][k] for r in runs]):.3f}±{np.std([r[split][k] for r in runs]):.3f}"
                                    for k in keys) + f"  (n={len(runs)})")
