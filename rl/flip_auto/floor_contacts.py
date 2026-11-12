"""Which robot bodies touch the floor in an eval record (or a reference)?  Replays the record's pelvis pose + joints
in the training model (sim2sim/models/flip.mjb) and lists, per step range, bodies whose collision geoms are within
--tol of the floor - e.g. a head / torso / knee contact that should never happen.
Usage (unitree_rl_mjlab env): python floor_contacts.py <flip_auto_*_record.npz> [first last] [--ref]"""
import argparse
from collections import defaultdict
from pathlib import Path

import mujoco
import numpy as np

ap = argparse.ArgumentParser()
ap.add_argument("rec")
ap.add_argument("first", type=int, nargs="?", default=0)
ap.add_argument("last", type=int, nargs="?", default=-1)
ap.add_argument("--ref", action="store_true", help="use the record's reference (qr / bpr / bqr) instead")
ap.add_argument("--tol", type=float, default=0.01)
a = ap.parse_args()
m = mujoco.MjModel.from_binary_path(str(Path(__file__).resolve().parents[2] / "sim2sim/models/flip.mjb"))
d = mujoco.MjData(m)
R = np.load(a.rec, allow_pickle=True)
q, bp, bq = (R["qr"], R["bpr"], R["bqr"]) if a.ref else (R["q"], R["bp"], R["bq"])
jn = [str(x) for x in R["joint_names"]]
mj = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
perm = [jn.index(n) for n in mj]
geoms = [g for g in range(m.ngeom) if m.body(m.geom_bodyid[g]).name.startswith("robot/")
         and (m.geom_contype[g] | m.geom_conaffinity[g])]
T = len(q)
last = T - 1 if a.last < 0 else a.last
touch = defaultdict(list)
low_min = defaultdict(lambda: 9.0)
for t in range(a.first, last + 1):
  d.qpos[:3], d.qpos[3:7], d.qpos[7:] = bp[t, 0], bq[t, 0], q[t][perm]
  mujoco.mj_kinematics(m, d)
  mujoco.mj_collision(m, d) if False else None
  for g in geoms:
    r = m.geom_rbound[g]
    if d.geom_xpos[g, 2] - r > a.tol:
      continue
    # exact lowest point for the common primitive types
    R3 = d.geom_xmat[g].reshape(3, 3)
    s, t_ = m.geom_size[g], m.geom_type[g]
    if t_ == mujoco.mjtGeom.mjGEOM_SPHERE:
      z = d.geom_xpos[g, 2] - s[0]
    elif t_ == mujoco.mjtGeom.mjGEOM_CAPSULE:
      z = d.geom_xpos[g, 2] - abs(R3[2, 2]) * s[1] - s[0]
    elif t_ == mujoco.mjtGeom.mjGEOM_BOX:
      z = d.geom_xpos[g, 2] - np.abs(R3[2] * s).sum()
    else:
      z = d.geom_xpos[g, 2] - r
    name = m.body(m.geom_bodyid[g]).name.replace("robot/", "")
    low_min[name] = min(low_min[name], z)
    if z < a.tol and t not in touch[name]:
      touch[name].append(t)
print(f"{'record reference' if a.ref else 'robot'} steps {a.first}-{last}: bodies within {a.tol * 100:.0f} cm of the floor")
for n, ts in sorted(touch.items(), key=lambda kv: kv[1][0]):
  runs, s = [], ts[0]
  for i in range(1, len(ts) + 1):
    if i == len(ts) or ts[i] != ts[i - 1] + 1:
      runs.append(f"{s}-{ts[i - 1]}" if ts[i - 1] > s else f"{s}")
      if i < len(ts):
        s = ts[i]
  print(f"  {n:28s} {len(ts):4d} steps: {', '.join(runs)}   lowest {low_min[n] * 100:+.1f} cm")
