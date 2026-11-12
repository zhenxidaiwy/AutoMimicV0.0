"""Frame-to-frame speeds of G1 reference csvs (30 fps): root vertical / horizontal speed and the fastest joint, to
find jumps introduced by a repair. Usage: python ref_speed.py <csv> [<csv> ...]  (prints frames with any jump)"""
import sys

import numpy as np

names = None
cs = [np.loadtxt(f, delimiter=",") for f in sys.argv[1:]]
print("frame | " + " | ".join(f"{f.split('/')[-1]}: vz vxy m/s, joint max rad/s (idx)" for f in sys.argv[1:]))
for t in range(len(cs[0]) - 1):
  row, flag = [], False
  for c in cs:
    v = (c[t + 1, :3] - c[t, :3]) * 30
    w = (c[t + 1, 7:] - c[t, 7:]) * 30
    j = int(np.argmax(np.abs(w)))
    row.append(f"{v[2]:+5.2f} {np.linalg.norm(v[:2]):5.2f} {w[j]:+6.1f} ({j})")
    flag |= abs(v[2]) > 1.5 or np.linalg.norm(v[:2]) > 2.5 or abs(w[j]) > 15
  if flag:
    print(f"{t:3d}->{t + 1:<3d} | " + " | ".join(row))
