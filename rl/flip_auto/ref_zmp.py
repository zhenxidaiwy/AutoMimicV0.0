"""Generic physics check of a reference: is each frame dynamically feasible with the contacts it has?
In the training model (sim2sim/models/flip.mjb): whole-body CoM c, total mass M, CoM acceleration a and the rate of
the centroidal angular momentum dL (finite differences of the reference at 50 fps). Flat floor at z = 0:
  ZMP p = c_xy - c_z * a_xy / (a_z + g) + (dL_x, -dL_y)... (standard cart-table form with angular momentum)
  required friction ratio |a_xy| / (a_z + g)
Support = collision geoms within --tol of the floor (feet AND hands); per frame the distance of the ZMP outside the
convex hull of their contact points (0 = inside). Airborne frames (no support) need a_z ~ -g instead.
Usage (unitree_rl_mjlab env): python ref_zmp.py <ref npz> [first last] [--tol 0.02]"""
import argparse
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial import ConvexHull, Delaunay

ap = argparse.ArgumentParser()
ap.add_argument("ref")
ap.add_argument("first", type=int, nargs="?", default=0)
ap.add_argument("last", type=int, nargs="?", default=-1)
ap.add_argument("--tol", type=float, default=0.02)
ap.add_argument("--sigma", type=float, default=3.0)
ap.add_argument("--labels", default=None, help="labels npz: per-phase summary")
ap.add_argument("--quiet", action="store_true", help="summary only")
a = ap.parse_args()
m = mujoco.MjModel.from_binary_path(str(Path(__file__).resolve().parents[2] / "sim2sim/models/flip.mjb"))
d = mujoco.MjData(m)
z = np.load(a.ref)
T = len(z["joint_pos"])
last = T - 1 if a.last < 0 else a.last
dt, g = 1 / 50.0, 9.81
ROOT = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "robot/pelvis")
M = m.body_subtreemass[ROOT]
robot_geoms = [i for i in range(m.ngeom) if m.body(m.geom_bodyid[i]).name.startswith("robot/")
               and (m.geom_contype[i] | m.geom_conaffinity[i])]


def lowest(gid):
  """lowest point (xyz) of a box / sphere / capsule / mesh-bounding geom."""
  R = d.geom_xmat[gid].reshape(3, 3)
  s, p = m.geom_size[gid], d.geom_xpos[gid]
  t = m.geom_type[gid]
  if t == mujoco.mjtGeom.mjGEOM_SPHERE:
    return p - [0, 0, s[0]]
  if t == mujoco.mjtGeom.mjGEOM_CAPSULE:
    ax = R[:, 2] * s[1]
    e = p + ax if (p + ax)[2] < (p - ax)[2] else p - ax
    return e - [0, 0, s[0]]
  if t == mujoco.mjtGeom.mjGEOM_BOX:
    corners = np.array([[i, j, k] for i in (-1, 1) for j in (-1, 1) for k in (-1, 1)]) * s
    w = p + corners @ R.T
    return w[w[:, 2].argmin()]
  r = m.geom_rbound[gid]
  return p - [0, 0, r]


com, L, sup = [], [], []
for t in range(T):
  d.qpos[:3], d.qpos[3:7], d.qpos[7:] = z["body_pos_w"][t, 0], z["body_quat_w"][t, 0], z["joint_pos"][t]
  d.qvel[:3] = z["body_lin_vel_w"][t, 0]
  # free-joint angular velocity is in the BODY frame: rotate the reference's world angular velocity into it
  qw = z["body_quat_w"][t, 0]
  Rb = np.zeros(9)
  mujoco.mju_quat2Mat(Rb, qw)
  d.qvel[3:6] = Rb.reshape(3, 3).T @ z["body_ang_vel_w"][t, 0]
  d.qvel[6:] = z["joint_vel"][t]
  mujoco.mj_forward(m, d)
  mujoco.mj_subtreeVel(m, d)
  com.append(d.subtree_com[ROOT].copy())
  L.append(d.subtree_angmom[ROOT].copy())
  pts, names = [], set()
  for gid in robot_geoms:
    lp = lowest(gid)
    if lp[2] < a.tol:
      pts.append(lp[:2])
      names.add(m.body(m.geom_bodyid[gid]).name.replace("robot/", "").replace("_link", ""))
  sup.append((np.array(pts), sorted(names)))
com, L = np.array(com), np.array(L)
# the 50 fps reference is interpolated from 30 fps: raw double differences are dominated by interpolation kinks, so
# smooth over --sigma frames (default 3 = 60 ms) before differentiating
from scipy.ndimage import gaussian_filter1d
cs = gaussian_filter1d(com, a.sigma, axis=0, mode="nearest") if a.sigma > 0 else com
Ls = gaussian_filter1d(L, a.sigma, axis=0, mode="nearest") if a.sigma > 0 else L
acc = np.gradient(np.gradient(cs, dt, axis=0), dt, axis=0)
dL = np.gradient(Ls, dt, axis=0)


def outside(p, pts):
  if len(pts) == 0:
    return np.inf
  if len(pts) < 3:
    return float(np.min(np.linalg.norm(pts - p, axis=1)))
  try:
    hull = ConvexHull(pts)
    if Delaunay(pts[hull.vertices]).find_simplex(p) >= 0:
      return 0.0
    v = pts[hull.vertices]
    segs = [(v[i], v[(i + 1) % len(v)]) for i in range(len(v))]
    dist = []
    for s0, s1 in segs:
      u = s1 - s0
      tt = np.clip(np.dot(p - s0, u) / max(np.dot(u, u), 1e-12), 0, 1)
      dist.append(np.linalg.norm(p - (s0 + tt * u)))
    return float(min(dist))
  except Exception:
    return float(np.min(np.linalg.norm(pts - p, axis=1)))


print(f"mass {M:.1f} kg; frame: support bodies | CoM z | a_z+g | friction ratio | ZMP outside support (m)")
rows = []
for t in range(a.first, last + 1):
  az = acc[t, 2] + g
  pts, names = sup[t]
  if az > 0.5:
    zmp = com[t, :2] - com[t, 2] * acc[t, :2] / az + np.array([-dL[t, 1], dL[t, 0]]) / (M * az)
    out = outside(zmp, pts)
  else:
    zmp, out = None, np.nan
  fr = np.linalg.norm(acc[t, :2]) / az if az > 0.5 else np.inf
  rows.append((t, out, fr, len(pts)))
  if not a.quiet:
    print(f"{t:4d}: {','.join(names) or 'NONE':45s} {com[t, 2]:.2f}  {az:6.2f}  {fr:5.2f}  "
          + ("airborne-ish" if zmp is None else ("no support" if np.isinf(out) else f"{out:.2f}")))
r = np.array([(o if np.isfinite(o) else 9.9, f) for _, o, f, _ in rows if not np.isnan(o)])
if len(r):
  print(f"frames with ZMP > 5 cm outside support: {int((r[:, 0] > 0.05).sum())} of {len(r)}; "
        f"> 20 cm: {int((r[:, 0] > 0.2).sum())}; friction ratio > 0.6: {int((r[:, 1] > 0.6).sum())}")
if a.labels:
  Lb = np.load(a.labels)
  names_, ph = [str(x) for x in Lb["phase_names"]], Lb["phase"]
  print("phase (frames): median / max ZMP outside support (m), frames > 20 cm, median friction ratio")
  for p in dict.fromkeys(ph[a.first:last + 1].tolist()):
    sel = [(o, f) for t, o, f, _ in rows if ph[t] == p and not np.isnan(o)]
    if sel:
      o = np.array([x[0] if np.isfinite(x[0]) else 9.9 for x in sel])
      f = np.array([x[1] for x in sel])
      print(f"  {names_[p]:10s} ({len(sel):3d}): {np.median(o):.2f} / {o.max():.2f}, {int((o > 0.2).sum())}, "
            f"{np.median(f):.2f}")
