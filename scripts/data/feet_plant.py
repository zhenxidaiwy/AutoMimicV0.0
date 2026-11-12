"""Generic reference repair: planted feet ON the floor and level in still-stance phases (legs + root height only).

ground_fix moves only the root (lowest planted sole -> z = 0), so with an uneven monocular stance the other planted
foot can float: cartwheel_2 kept the right sole 2.4-3.1 cm above the floor for the whole held final pose and the left
sole 2.8-3.8 cm up in the first stand - on a fully STRAIGHT leg (knee 0.01-0.08 rad, hip-ankle = straight length)
while the other knee was bent 0.6-0.8 rad, so the leg cannot reach the floor with the pelvis where it is.
For every frame of the chosen phases (default: stand) with a planted foot, the root HEIGHT (nothing else of the root)
and the planted legs' 6 joints are re-solved (bounded least squares): each planted foot level (roll / pitch 0, own
yaw kept), sole spheres at z = 0, xy unchanged; planted knees >= --knee_min (no locked-straight knee); small root /
joint changes preferred. Waist and arm joints and the root xy / orientation are NOT touched. The change fades out
linearly over --ramp frames outside the phase.

Usage (gmr env): python feet_plant.py <clip_id> [--src lock_vlm] [--phases stand] [--ramp 6] [--knee_min 0.1]
Input data/g1/<clip>/g1_<src>.csv -> output g1_plant_vlm.csv (+ .json report)"""
import argparse
import json
import os

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from ground_fix import FEET, XML, sole_heights

H = os.path.expanduser("~")
LEG = ("hip_pitch", "hip_roll", "hip_yaw", "knee", "ankle_pitch", "ankle_roll")

ap = argparse.ArgumentParser()
ap.add_argument("clip_id")
ap.add_argument("--src", default="lock_vlm")
ap.add_argument("--phases", default="stand", help="comma-separated annotation phases")
ap.add_argument("--ramp", type=int, default=6)
ap.add_argument("--knee_min", type=float, default=0.1)
ap.add_argument("--out", default="plant_vlm", help="output stem: g1_<out>.csv")
a = ap.parse_args()
g = f"{H}/projects/dance/data/g1/{a.clip_id}"
csv = np.loadtxt(f"{g}/g1_{a.src}.csv", delimiter=",")
qpos = np.concatenate([csv[:, :3], csv[:, [6, 3, 4, 5]], csv[:, 7:]], 1)
T = len(qpos)
m = mujoco.MjModel.from_xml_path(XML)
d = mujoco.MjData(m)
ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
contact = np.stack([ann["contact_L"], ann["contact_R"]], 1)[:T]
in_ph = np.isin(np.array(ann["phase"][:T]), a.phases.split(","))
bid = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f) for f in FEET]
jid = [[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{s}_{j}_joint") for j in LEG] for s in ("left", "right")]
qadr = [[int(m.jnt_qposadr[i]) for i in js] for js in jid]

q0 = np.zeros(m.nq)
q0[2], q0[3] = 1.0, 1.0
d.qpos[:] = q0
mujoco.mj_kinematics(m, d)
h0 = d.xpos[bid, 2] - sole_heights(m, q0[None])[0][0]   # ankle height of a level foot with the sole on the floor


def put(q):
  d.qpos[:] = q
  mujoco.mj_kinematics(m, d)


new = qpos.copy()
mask = np.zeros(T, bool)
for t in range(T):
  legs = [j for j in range(2) if in_ph[t] and contact[t, j] == 1]
  if not legs:
    continue
  mask[t] = True
  put(qpos[t])
  tgt = []
  for j in legs:
    R = d.xmat[bid[j]].reshape(3, 3)
    tgt.append((np.array([d.xpos[bid[j], 0], d.xpos[bid[j], 1], h0[j]]),
                Rotation.from_euler("z", np.arctan2(R[1, 0], R[0, 0]))))
  ad = sum((qadr[j] for j in legs), [])
  lo = np.concatenate([[-0.08]] + [m.jnt_range[jid[j], 0] for j in legs])
  hi = np.concatenate([[0.02]] + [m.jnt_range[jid[j], 1] for j in legs])
  for k, j in enumerate(legs):  # planted knee not locked straight
    lo[1 + 6 * k + 3] = max(lo[1 + 6 * k + 3], a.knee_min)
  x0 = np.concatenate([[0.0], qpos[t, ad]])

  def res(x):
    q = qpos[t].copy()
    q[2] += x[0]
    q[ad] = x[1:]
    put(q)
    r = []
    for j, (tp, tR) in zip(legs, tgt):
      r += [10 * (d.xpos[bid[j]] - tp), 2 * (tR.inv() * Rotation.from_matrix(d.xmat[bid[j]].reshape(3, 3))).as_rotvec()]
    return np.concatenate(r + [[0.1 * x[0]], 0.02 * (x[1:] - x0[1:])])
  x = least_squares(res, np.clip(x0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi)).x
  new[t, 2] += x[0]
  new[t, ad] = x[1:]

# fade the change out over --ramp frames on both sides of each solved run
delta = new - qpos
idx = np.where(mask)[0]
out = new.copy()
if len(idx):
  for t in range(T):
    if mask[t]:
      continue
    k = idx[np.abs(idx - t).argmin()]
    out[t] = qpos[t] + max(0.0, 1.0 - abs(t - k) / (a.ramp + 1)) * delta[k]
out[:, 3:7] = qpos[:, 3:7]                      # root orientation never changed
sb, _ = sole_heights(m, qpos)
sa, _ = sole_heights(m, out)
pl = (contact == 1) & mask[:, None]
fixed = np.concatenate([out[:, :3], out[:, [4, 5, 6, 3]], out[:, 7:]], 1)
dst = f"{g}/g1_{a.out}.csv"
np.savetxt(dst, fixed.astype(np.float32), delimiter=",")
legs_ad = sum(qadr, [])
other = [i for i in range(7, m.nq) if i not in legs_ad]
rep = {"clip": a.clip_id, "src": a.src, "phases": a.phases, "frames_solved": int(mask.sum()),
       "level_ankle_z_m": [round(float(x), 4) for x in h0],
       "planted_sole_z_cm max|.| before (L,R)": [round(float(np.abs(sb[pl[:, j], j]).max() * 100), 2) for j in range(2)],
       "planted_sole_z_cm max|.| after (L,R)": [round(float(np.abs(sa[pl[:, j], j]).max() * 100), 2) for j in range(2)],
       "sole_min_cm_after": round(float(sa.min() * 100), 2),
       "root_z_change_cm (min,max)": [round(float((out[:, 2] - qpos[:, 2]).min() * 100), 2),
                                      round(float((out[:, 2] - qpos[:, 2]).max() * 100), 2)],
       "leg_joint_change_rad_max": round(float(np.abs(out[:, legs_ad] - qpos[:, legs_ad]).max()), 3),
       "root_xy_orientation_waist_arms_max_change": float(max(np.abs(out[:, :2] - qpos[:, :2]).max(),
                                                              np.abs(out[:, 3:7] - qpos[:, 3:7]).max(),
                                                              np.abs(out[:, other] - qpos[:, other]).max()))}
json.dump(rep, open(dst.replace(".csv", ".json"), "w"), indent=1)
print(json.dumps(rep))
