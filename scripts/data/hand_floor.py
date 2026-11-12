"""Lowest point of each hand (mjlab G1 hand collision capsule, wrist_yaw frame) and each sole above the floor, per
frame, for a G1 csv; plus the human's hand height in GMR's scaled targets is not needed - the floor is z=0.
Usage (gmr env): python hand_floor.py <csv> [every=2]"""
import sys

import mujoco
import numpy as np

sys.path.insert(0, "/home/user/dance_win/scripts/data")
from contact_lock import EFF, Geo  # noqa: E402

c = np.loadtxt(sys.argv[1], delimiter=",")
every = int(sys.argv[2]) if len(sys.argv) > 2 else 2
q = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)
geo = Geo(mujoco.MjModel.from_xml_path("/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"))
L = np.array([[geo.frame(x)[n][2] for n in EFF] for x in q])
print("frame  sole L  sole R  hand L  hand R  (lowest point above the floor, m)  root z")
for t in range(0, len(q), every):
  print(f"{t:5d}  {L[t,0]:6.3f}  {L[t,1]:6.3f}  {L[t,2]:6.3f}  {L[t,3]:6.3f}   {c[t,2]:.3f}")
