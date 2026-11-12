"""Per-frame contact geometry of a retargeted G1 reference (any skill): ankle / wrist heights above the floor, root
height, torso tilt and cumulative rotation about the dominant axis. Used to label contacts (VLM + geometry) and to
spot reference errors (hands in the floor during support, feet sliding, ...).
Usage (gmr env): python ref_contacts.py <g1 csv> [every=1]"""
import sys

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation as R

XML = "/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"
c = np.loadtxt(sys.argv[1], delimiter=",")
every = int(sys.argv[2]) if len(sys.argv) > 2 else 1
qpos = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)  # csv xyz, quat xyzw -> wxyz
m = mujoco.MjModel.from_xml_path(XML)
d = mujoco.MjData(m)
names = ["left_ankle_roll_link", "right_ankle_roll_link", "left_wrist_yaw_link", "right_wrist_yaw_link", "torso_link"]
ids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, n) for n in names]
P, Q = [], []
for q in qpos:
  d.qpos[:] = q
  mujoco.mj_kinematics(m, d)
  P.append(d.xpos[ids].copy())
  Q.append(d.xquat[ids[-1]].copy())
P, Q = np.array(P), np.array(Q)
rot = R.from_quat(Q[:, [1, 2, 3, 0]])
inc = (rot[:-1].inv() * rot[1:]).as_rotvec()
ax = inc.sum(0)
ax /= np.linalg.norm(ax) + 1e-9
cum = np.degrees(np.concatenate([[0], np.cumsum(inc @ ax)]))
up = rot.apply([0, 0, 1])[:, 2]
tilt = np.degrees(np.arccos(np.clip(up, -1, 1)))
print(f"frames {len(c)}; rotation axis (torso frame, summed) {np.round(ax, 2)}; total rotation {cum[-1]:.0f} deg")
print("frame  ankleL ankleR  wristL wristR  root_z  tilt  rot")
for t in range(0, len(c), every):
  print(f"{t:5d}  {P[t,0,2]:6.3f} {P[t,1,2]:6.3f}  {P[t,2,2]:6.3f} {P[t,3,2]:6.3f}  {c[t,2]:6.3f} {tilt[t]:5.0f} {cum[t]:5.0f}")
