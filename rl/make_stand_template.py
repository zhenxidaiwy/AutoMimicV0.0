"""Build the canonical standing template (mjlab G1 KNEES_BENT_KEYFRAME, the robot's default standing pose):
positions of key bodies relative to the ankle midpoint, expressed in the pelvis yaw frame.
Usage (gmr env, has mujoco): python make_stand_template.py  -> ~/dance_win/rl/getup/stand_template.npz
"""
import os
from pathlib import Path

import mujoco
import numpy as np

KEYFRAME = {"hip_pitch": -0.312, "knee": 0.669, "ankle_pitch": -0.363, "elbow": 0.6,
            "left_shoulder_roll": 0.2, "left_shoulder_pitch": 0.2, "right_shoulder_roll": -0.2,
            "right_shoulder_pitch": 0.2}
PELVIS_Z = 0.76
# shoulders sit high on the torso, so a leaning torso moves them a lot (torso_link's origin is at the waist and
# barely moves when the torso tilts)
BODIES = ("pelvis", "left_shoulder_pitch_link", "right_shoulder_pitch_link", "left_knee_link", "right_knee_link",
          "left_ankle_roll_link", "right_ankle_roll_link", "left_wrist_yaw_link", "right_wrist_yaw_link")
# Positions are relative to the midpoint of the two ankles (a point on the ground under the robot), not the pelvis:
# relative to the pelvis, a tilted pelvis plus a counter-bent waist partly cancel (v6c: 19 deg torso lean but only
# 7 cm template error).

if __name__ == "__main__":
  here = Path(__file__).resolve().parent
  os.chdir(here.parent / "live" / "g1")
  m = mujoco.MjModel.from_xml_path("scene_live.xml")
  d = mujoco.MjData(m)
  d.qpos[:3] = [0, 0, PELVIS_Z]
  d.qpos[3:7] = [1, 0, 0, 0]
  for j in range(m.njnt):
    name = m.joint(j).name
    if name == "floating_base_joint":
      continue
    for k, v in KEYFRAME.items():
      if name.endswith(k + "_joint") and (name.startswith(("left", "right")) == k.startswith(("left", "right")) or
                                          not k.startswith(("left", "right"))):
        d.qpos[m.jnt_qposadr[j]] = v
  mujoco.mj_kinematics(m, d)
  origin = (d.body("left_ankle_roll_link").xpos + d.body("right_ankle_roll_link").xpos) / 2
  rel = np.stack([d.body(b).xpos - origin for b in BODIES])
  np.savez(here / "getup" / "stand_template.npz", bodies=np.array(BODIES), rel_pos=rel, pelvis_z=PELVIS_Z)
  for b, r in zip(BODIES, rel):
    print(f"{b:<24} {np.round(r, 3)}")
  print("knee joint check:", round(float(d.qpos[m.jnt_qposadr[m.joint('left_knee_joint').id]]), 3),
        "| feet z:", round(float(d.body('left_ankle_roll_link').xpos[2]), 3))
