"""Robot vs reference joint table for chosen steps: python3 joint_table.py <record.npz> <first> <last> <step> joint ...
(joint names without the _joint suffix; 'L:'/'R:' prefixes not needed - both sides are printed)"""
import sys

import numpy as np

R = np.load(sys.argv[1], allow_pickle=True)
a, b, s = int(sys.argv[2]), int(sys.argv[3]), int(sys.argv[4])
bases = sys.argv[5:]
jn = [str(x) for x in R["joint_names"]]
q, qr = R["q"], R["qr"]
cols = []
for base in bases:
  for side in ("left", "right"):
    n = f"{side}_{base}_joint" if f"{side}_{base}_joint" in jn else f"{base}_joint"
    if n in jn and n not in cols:
      cols.append(n)
print("step " + " ".join(f"{c.replace('_joint', '')[:16]:>17s}" for c in cols) + "   (robot/ref rad)")
for t in range(a, min(b + 1, len(q)), s):
  print(f"{t:4d} " + " ".join(f"{q[t, jn.index(c)]:+6.2f}/{qr[t, jn.index(c)]:+6.2f}    " for c in cols))
