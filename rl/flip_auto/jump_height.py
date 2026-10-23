"""Pelvis height robot vs reference around the flip, from eval records: python jump_height.py <record.npz> ..."""
import sys

import numpy as np

for p in sys.argv[1:]:
  R = np.load(p, allow_pickle=True)
  bn = [str(x) for x in R["body_names"]]
  i = bn.index("pelvis") if "pelvis" in bn else 0
  z, zr = R["bp"][:, i, 2], R["bpr"][:, i, 2]
  print(p.split("/")[-3][-13:], f"robot peak {z[80:130].max():.3f} m (step {80 + z[80:130].argmax()}), "
        f"ref peak {zr[80:130].max():.3f} m (step {80 + zr[80:130].argmax()}); stand height before: robot {z[60]:.3f} ref {zr[60]:.3f}")
