"""Print the body / joint layout of the exported runtime model (which body is the pelvis, qpos size)."""
from pathlib import Path

import mujoco

m = mujoco.MjModel.from_binary_path(str(Path.home() / "dance_win/sim2sim/models/dance.mjb"))
print("nq", m.nq, "nv", m.nv, "nu", m.nu, "nbody", m.nbody, "njnt", m.njnt)
for b in range(min(m.nbody, 6)):
  print("body", b, m.body(b).name, "parent", m.body_parentid[b], "subtreemass", round(m.body_subtreemass[b], 2))
for j in range(min(m.njnt, 4)):
  print("joint", j, m.joint(j).name, "type", m.jnt_type[j], "qposadr", m.jnt_qposadr[j], "body", m.jnt_bodyid[j])
