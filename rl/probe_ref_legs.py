"""Reference hip roll / yaw and knee separation during flight (are the twist limits feasible for the reference?)."""
from pathlib import Path

import mujoco
import numpy as np

H = Path.home()
m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
d = mujoco.MjData(m)
names = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
z = np.load(H / "projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz")
lab = np.load(H / "projects/dance/dataset/backflip_3/labels_50fps.npz")
pn = [str(x) for x in lab["phase_names"]]
fl = np.where(lab["phase"] == pn.index("flight"))[0]
ld = np.where(lab["phase"] == pn.index("land"))[0]
win = np.arange(fl[0], min(ld[0] + 10, len(lab["phase"])))
idx = {n: names.index(n) for n in ("left_hip_roll_joint", "right_hip_roll_joint", "left_hip_yaw_joint", "right_hip_yaw_joint")}
q = z["joint_pos"][win]
print({n: round(float(np.abs(q[:, i]).max()), 2) for n, i in idx.items()})
kn = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"robot/{s}_knee_link") for s in ("left", "right")]
seps = []
for f in win:
  d.qpos[:3] = z["body_pos_w"][f, 0]
  d.qpos[3:7] = z["body_quat_w"][f, 0]
  d.qpos[7:] = z["joint_pos"][f]
  mujoco.mj_kinematics(m, d)
  R = d.xmat[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "robot/pelvis")].reshape(3, 3)
  seps.append(abs((d.xpos[kn[0]] - d.xpos[kn[1]]) @ R[:, 1]))
print("reference knee separation in flight: max", round(max(seps), 3), "min", round(min(seps), 3))
