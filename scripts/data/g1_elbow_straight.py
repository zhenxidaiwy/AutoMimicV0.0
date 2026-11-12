"""G1 elbow joint value of a straight arm (bend 0 deg between shoulder_yaw -> elbow -> wrist_roll), by sweeping the
joint over its range on the GMR model. Usage (gmr env): python g1_elbow_straight.py"""
import mujoco
import numpy as np

m = mujoco.MjModel.from_xml_path("/home/user/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml")
d = mujoco.MjData(m)
for side, j in (("left", 18), ("right", 25)):
  ids = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{side}_{b}") for b in ("shoulder_yaw_link", "elbow_link", "wrist_roll_link")]
  best = None
  for q in np.linspace(m.jnt_range[j + 1, 0], m.jnt_range[j + 1, 1], 300):
    d.qpos[:] = 0
    d.qpos[3] = 1
    d.qpos[7 + j] = q
    mujoco.mj_kinematics(m, d)
    a, b = d.xpos[ids[0]] - d.xpos[ids[1]], d.xpos[ids[2]] - d.xpos[ids[1]]
    bend = 180 - np.degrees(np.arccos(np.clip(a @ b / np.linalg.norm(a) / np.linalg.norm(b), -1, 1)))
    if best is None or bend < best[1]:
      best = (q, bend)
  print(side, "straight at q =", round(float(best[0]), 3), "bend", round(float(best[1]), 1), "deg; range", m.jnt_range[j + 1])
