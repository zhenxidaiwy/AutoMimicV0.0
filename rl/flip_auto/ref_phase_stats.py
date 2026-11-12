"""Per-phase statistics of a 50 fps reference (any skill): torso tilt, horizontal ankle distance, pelvis height and
waist yaw, so termination thresholds can be set relative to what the reference itself does.
Usage (unitree_rl_mjlab or gmr env): python ref_phase_stats.py <ref npz> <labels npz>"""
import sys

import numpy as np

z = np.load(sys.argv[1])
L = np.load(sys.argv[2])
names = [str(x) for x in L["phase_names"]]
ph = L["phase"][:len(z["joint_pos"])]
bq, bp = z["body_quat_w"], z["body_pos_w"]
# body order of the mjlab G1 motion npz (30 bodies): 0 pelvis ... ; ankle_roll = 6 / 12, torso = 15 in mjlab order
ANK = (6, 12)
TORSO = 15
q = bq[:, TORSO]
up = 1 - 2 * (q[:, 1] ** 2 + q[:, 2] ** 2)
tilt = np.degrees(np.arccos(np.clip(up, -1, 1)))
feet = np.linalg.norm(bp[:, ANK[0], :2] - bp[:, ANK[1], :2], axis=-1)
pel = bp[:, 0, 2]
s = 0
print("phase          frames      tilt deg (min/max)  feet dist m (min/max)  pelvis z (min/max)")
for i in range(1, len(ph) + 1):
  if i == len(ph) or ph[i] != ph[s]:
    sl = slice(s, i)
    print(f"{names[ph[s]]:12s} {s:4d}-{i - 1:<4d}   {tilt[sl].min():5.0f} {tilt[sl].max():5.0f}          "
          f"{feet[sl].min():5.2f} {feet[sl].max():5.2f}            {pel[sl].min():5.2f} {pel[sl].max():5.2f}")
    s = i
