"""GVHMR in-camera orientation of a clip: unwrapped rotation and per-frame angle relative to frame 0 + bbox info."""
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.spatial.transform import Rotation as R

D = Path.home() / "projects/dance/data/gvhmr"
cid = sys.argv[1]
h = torch.load(D / cid / "hmr4d_results.pt", map_location="cpu", weights_only=False)
print("keys", list(h.keys()))
for key in ("smpl_params_incam", "smpl_params_global"):
  go = h[key]["global_orient"].numpy()
  r = R.from_rotvec(go)
  inc = (r[:-1].inv() * r[1:]).as_rotvec()
  step = np.degrees(np.linalg.norm(inc, axis=-1))
  print(key, "frames", len(go), "sum |step| deg", step.sum().round(1), "max step", step.max().round(1),
        "angle to frame0 every 5:", np.degrees(np.linalg.norm((r[0].inv() * r).as_rotvec(), axis=-1))[::5].round(0).tolist())
pre = D / cid / "preprocess"
for f in sorted(pre.glob("*")) if pre.exists() else []:
  print("preprocess", f.name)
bb = pre / "bbx.pt"
if bb.exists():
  b = torch.load(bb, map_location="cpu", weights_only=False)
  x = b["bbx_xys"].numpy() if "bbx_xys" in b else None
  if x is not None:
    print("bbx size every 5 frames", x[::5, 2].round(0).tolist())
