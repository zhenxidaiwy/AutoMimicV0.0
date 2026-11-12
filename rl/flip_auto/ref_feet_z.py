"""Lowest foot-geom height of each foot over a reference, in the training model (sim2sim/models/flip.mjb): is the
reference standing ON the floor (about 0) or floating / sinking?
Usage (unitree_rl_mjlab env): python ref_feet_z.py <ref npz> [step]"""
import sys
from pathlib import Path

import mujoco
import numpy as np

m = mujoco.MjModel.from_binary_path(str(Path(__file__).resolve().parents[2] / "sim2sim/models/flip.mjb"))
d = mujoco.MjData(m)
z = np.load(sys.argv[1])
step = int(sys.argv[2]) if len(sys.argv) > 2 else 10
feet = {s: [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.endswith(f"{s}_ankle_roll_link")
            and m.geom_contype[g] | m.geom_conaffinity[g]] for s in ("left", "right")}


def low(g):
  """lowest point of a box / sphere / capsule geom (world z)."""
  R = d.geom_xmat[g].reshape(3, 3)
  s = m.geom_size[g]
  if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_BOX:
    return d.geom_xpos[g][2] - np.abs(R[2] * s).sum()
  if m.geom_type[g] == mujoco.mjtGeom.mjGEOM_CAPSULE:
    return d.geom_xpos[g][2] - abs(R[2, 2]) * s[1] - s[0]
  return d.geom_xpos[g][2] - s[0]


print("frame  left foot z (cm)  right foot z (cm)")
for t in range(0, len(z["joint_pos"]), step):
  d.qpos[:3], d.qpos[3:7], d.qpos[7:] = z["body_pos_w"][t, 0], z["body_quat_w"][t, 0], z["joint_pos"][t]
  mujoco.mj_kinematics(m, d)
  print(f"{t:5d}  {min(low(g) for g in feet['left']) * 100:8.1f}  {min(low(g) for g in feet['right']) * 100:8.1f}")
