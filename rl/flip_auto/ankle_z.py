"""Ankle heights (body origin, m) robot vs reference and knee angles over a step range of an eval record.
Usage: python ankle_z.py <record.npz> first last"""
import sys

import numpy as np

R = np.load(sys.argv[1], allow_pickle=True)
a, b = int(sys.argv[2]), int(sys.argv[3])
bn = [str(x) for x in R["body_names"]]
jn = [str(x) for x in R["joint_names"]]
L, Rr = bn.index("left_ankle_roll_link"), bn.index("right_ankle_roll_link")
kl, kr = jn.index("left_knee_joint"), jn.index("right_knee_joint")
print("step  L ankle z robot/ref   R ankle z robot/ref   L knee robot/ref   R knee robot/ref")
for t in range(a, b + 1):
  print(f"{t:4d}   {R['bp'][t, L, 2]:.3f}/{R['bpr'][t, L, 2]:.3f}        {R['bp'][t, Rr, 2]:.3f}/{R['bpr'][t, Rr, 2]:.3f}"
        f"        {R['q'][t, kl]:+.2f}/{R['qr'][t, kl]:+.2f}      {R['q'][t, kr]:+.2f}/{R['qr'][t, kr]:+.2f}")
