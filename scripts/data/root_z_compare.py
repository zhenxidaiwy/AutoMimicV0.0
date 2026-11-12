"""Root height of several csv variants of a clip over a frame range, with the vertical acceleration (m/s^2, 30 fps
second difference) - where does a repair step introduce a vertical jerk?
Usage: python root_z_compare.py <clip> <first> <last> variant ...   (variant = csv stem in data/g1/<clip>/)"""
import json
import os
import sys

import numpy as np

H = os.path.expanduser("~")
clip, a, b = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
vs = sys.argv[4:]
z = {v: np.loadtxt(f"{H}/projects/dance/data/g1/{clip}/{v}.csv", delimiter=",")[:, 2] for v in vs}
acc = {v: np.gradient(np.gradient(x, 1 / 30), 1 / 30) for v, x in z.items()}
ann = json.load(open(f"{H}/dance_win/data/annotations/{clip}.json", encoding="utf-8"))
lab = lambda t: "".join(c for c, k in (("L", "contact_L"), ("R", "contact_R"), ("l", "hand_L"), ("r", "hand_R"))
                        if ann.get(k, [0] * 999)[t] == 1)
print("frame phase  contacts " + " ".join(f"{v[:14]:>22s}" for v in vs) + "   (root z m / a_z m/s^2)")
for t in range(a, b + 1):
  print(f"{t:4d} {ann['phase'][t][:7]:7s} {lab(t):5s} " + " ".join(f"{z[v][t]:8.3f} {acc[v][t]:+8.1f}    " for v in vs))
