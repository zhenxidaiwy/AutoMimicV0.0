"""Reference numbers for the G1 default standing keyframe (same frames as stance_check.py)."""
import math
from pathlib import Path

import mujoco
import numpy as np

if __name__ == "__main__":
  import os
  os.chdir(Path(__file__).resolve().parent.parent / "live" / "g1")
  m = mujoco.MjModel.from_xml_path("scene_live.xml")
  d = mujoco.MjData(m)
  print("keyframes:", [m.key(i).name for i in range(m.nkey)])
  if m.nkey:
    mujoco.mj_resetDataKeyframe(m, d, 0)
  else:
    d.qpos[2] = 0.8
  mujoco.mj_forward(m, d)
  def tilt(body):
    R = d.body(body).xmat.reshape(3, 3)
    return math.degrees(math.acos(np.clip(R[2, 2], -1, 1)))
  lf, rf, pel = d.body("left_ankle_roll_link").xpos, d.body("right_ankle_roll_link").xpos, d.body("pelvis").xpos
  print(f"torso tilt {tilt('torso_link'):.1f} deg | pelvis tilt {tilt('pelvis'):.1f} deg | pelvis z {pel[2]:.3f}")
  print(f"stance width {abs(lf[1] - rf[1]):.3f} m | fore-aft split {abs(lf[0] - rf[0]):.3f} m")
  for j in ("waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint", "left_knee_joint", "left_hip_pitch_joint"):
    print(f"  {j}: {d.qpos[m.jnt_qposadr[m.joint(j).id]]:.3f}")
  # torso frame vs world when waist joints are zero: show torso local z axis in world
  print("torso z axis in world:", np.round(d.body("torso_link").xmat.reshape(3, 3)[:, 2], 3))
