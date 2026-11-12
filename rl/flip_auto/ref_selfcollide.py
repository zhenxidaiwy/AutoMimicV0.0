"""Generic check: does the reference put the robot in self-collision (or below the floor) in the TRAINING model?
Poses the exported mjlab G1 model (sim2sim/models/flip.mjb, same collision setup as training) at every reference
frame and lists robot-robot contacts with penetration depth.
Usage (unitree_rl_mjlab env): python ref_selfcollide.py <ref npz> [first last]"""
import sys
from collections import defaultdict
from pathlib import Path

import mujoco
import numpy as np

m = mujoco.MjModel.from_binary_path(str(Path(__file__).resolve().parents[2] / "sim2sim/models/flip.mjb"))
d = mujoco.MjData(m)
z = np.load(sys.argv[1])
n = len(z["joint_pos"])
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, n - 1)
floor = {i for i in range(m.ngeom) if m.geom_bodyid[i] == 0}
pairs = defaultdict(list)
for t in range(a, b + 1):
  d.qpos[:3] = z["body_pos_w"][t, 0]
  d.qpos[3:7] = z["body_quat_w"][t, 0]
  d.qpos[7:] = z["joint_pos"][t]
  mujoco.mj_forward(m, d)
  for c in d.contact[:d.ncon]:
    if c.geom1 in floor or c.geom2 in floor:
      continue
    b1, b2 = m.body(m.geom_bodyid[c.geom1]).name, m.body(m.geom_bodyid[c.geom2]).name
    pairs[(b1, b2)].append((t, -c.dist))
print(f"frames {a}-{b}: {len(pairs)} self-contact body pairs")
for (b1, b2), v in sorted(pairs.items(), key=lambda kv: -max(x[1] for x in kv[1])):
  ts = [x[0] for x in v]
  print(f"  {b1:28s} {b2:28s} {len(v):4d} frames ({ts[0]}-{ts[-1]}), max penetration {max(x[1] for x in v) * 100:.1f} cm")
