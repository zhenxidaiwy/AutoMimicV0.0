"""Per tracked body: lowest origin height of the robot vs the reference over a step range of an eval record (where
does the robot go lower than the reference ever does, e.g. head / elbows on the floor?).
Usage: python body_min_z.py <record.npz> [first last]"""
import sys

import numpy as np

R = np.load(sys.argv[1], allow_pickle=True)
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, len(R["bp"]) - 1)
names = [str(x) for x in R["body_names"]]
print("body                         robot min z (step)   reference min z (step)   robot - ref (m)")
for i, n in enumerate(names):
  zr, zf = R["bp"][a:b + 1, i, 2], R["bpr"][a:b + 1, i, 2]
  print(f"{n:28s} {zr.min():6.3f} ({a + zr.argmin():3d})       {zf.min():6.3f} ({a + zf.argmin():3d})        {zr.min() - zf.min():+.3f}")
