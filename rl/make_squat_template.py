"""Build a deep-squat transition template for the get-up (human-like: lying -> squat -> stand).
Feet flat and side by side (pelvis level: hip_pitch + knee + ankle_pitch = 0), torso leaned forward with the waist
and arms forward so the whole-body CoM is above the feet. Prints the CoM margin for a few candidate squats and saves
the chosen one in the same format as stand_template.npz (key bodies relative to the ankle midpoint).
Usage (gmr env, has mujoco): python make_squat_template.py [--save K]
"""
import argparse
import os
from pathlib import Path

import mujoco
import numpy as np

from make_stand_template import BODIES

# (knee, ankle_pitch, waist_pitch, shoulder_pitch); hip_pitch = -(knee + ankle) keeps the feet flat
CANDIDATES = [
  (1.6, -0.70, 0.40, -0.8),
  (1.8, -0.75, 0.45, -1.0),
  (2.0, -0.80, 0.50, -1.2),
  (2.2, -0.85, 0.52, -1.3),
]
FOOT_FRONT, FOOT_BACK = 0.12, -0.05  # approx. sole extent along x relative to the ankle (G1 foot)


def pose(m, d, knee, ankle, waist, shoulder):
  mujoco.mj_resetData(m, d)
  d.qpos[3:7] = [1, 0, 0, 0]
  vals = {"hip_pitch": -(knee + ankle), "knee": knee, "ankle_pitch": ankle, "waist_pitch": waist,
          "shoulder_pitch": shoulder, "elbow": 0.6}
  for j in range(m.njnt):
    name = m.joint(j).name
    for k, v in vals.items():
      if name.endswith(k + "_joint"):
        lo, hi = m.jnt_range[j]
        d.qpos[m.jnt_qposadr[j]] = np.clip(v, lo, hi)
  d.qpos[2] = 1.0
  mujoco.mj_kinematics(m, d)
  mujoco.mj_comPos(m, d)
  foot_z = (d.body("left_ankle_roll_link").xpos[2] + d.body("right_ankle_roll_link").xpos[2]) / 2
  d.qpos[2] = 1.0 - (foot_z - 0.038)  # ankles at their standing height above the floor
  mujoco.mj_kinematics(m, d)
  mujoco.mj_comPos(m, d)
  origin = (d.body("left_ankle_roll_link").xpos + d.body("right_ankle_roll_link").xpos) / 2
  com = d.subtree_com[0] - origin
  return d.qpos[2], com, np.stack([d.body(b).xpos - origin for b in BODIES])


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--save", type=int, default=None, help="index of the candidate to save")
  a = ap.parse_args()
  here = Path(__file__).resolve().parent
  os.chdir(here.parent / "live" / "g1")
  m = mujoco.MjModel.from_xml_path("scene_live.xml")
  d = mujoco.MjData(m)
  for i, c in enumerate(CANDIDATES):
    pz, com, rel = pose(m, d, *c)
    inside = FOOT_BACK < com[0] < FOOT_FRONT
    print(f"[{i}] knee {c[0]:.2f} ankle {c[1]:.2f} hip {-(c[0] + c[1]):.2f} waist {c[2]:.2f} shoulder {c[3]:.2f} | "
          f"pelvis z {pz:.3f} m | CoM x vs ankles {com[0]:+.3f} m ({'over the feet' if inside else 'OUTSIDE'})")
  if a.save is not None:
    pz, com, rel = pose(m, d, *CANDIDATES[a.save])
    np.savez(here / "getup" / "squat_template.npz", bodies=np.array(BODIES), rel_pos=rel, pelvis_z=pz,
             joints=np.array(CANDIDATES[a.save]))
    for b, r in zip(BODIES, rel):
      print(f"{b:<26} {np.round(r, 3)}")
    print("saved squat_template.npz")
