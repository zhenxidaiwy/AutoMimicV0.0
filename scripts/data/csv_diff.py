"""Per-frame difference of two G1 csv variants of a clip: root shift (cm), max joint change (rad, joint) and which
joints changed most overall.  Usage (gmr env): python csv_diff.py <a.csv> <b.csv> [step]"""
import sys

import mujoco
import numpy as np

m = mujoco.MjModel.from_xml_path("/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml")
jn = [m.joint(i).name.replace("_joint", "") for i in range(1, m.njnt)]
A, B = np.loadtxt(sys.argv[1], delimiter=","), np.loadtxt(sys.argv[2], delimiter=",")
step = int(sys.argv[3]) if len(sys.argv) > 3 else 2
dr = np.linalg.norm(A[:, :3] - B[:, :3], axis=1) * 100
dj = np.abs(A[:, 7:] - B[:, 7:])
print("frame  root shift cm  max joint change rad (joint)")
for t in range(0, len(A), step):
  k = int(dj[t].argmax())
  print(f"{t:5d}  {dr[t]:8.2f}      {dj[t, k]:.3f} ({jn[k]})")
print("largest mean change:", ", ".join(f"{jn[k]} {dj[:, k].mean():.3f}" for k in np.argsort(-dj.mean(0))[:8]))
arms = [i for i, n in enumerate(jn) if any(s in n for s in ("shoulder", "elbow", "wrist"))]
print(f"arm joints max change {dj[:, arms].max():.4f} rad")
