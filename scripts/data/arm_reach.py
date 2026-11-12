"""Generic reference repair for hand-supported skills: planted hands ON the floor by the ARM joints only.

The G1 arm is shorter relative to the body than the human's (GMR scales 0.8 vs 0.9 for the legs), so with a smooth
root the robot's palm stays 6-25 cm above the floor in frames where the human's palm is planted (cartwheel_2: the
left palm reached the floor ~0.25 s after the human's, so the reference had to hover horizontally over one foot -
the policy lost the reference exactly there, r02 segment probe). For every frame labelled hand-planted with the hand
capsule above --tol, that arm's 7 joints (shoulder pitch / roll / yaw, elbow, wrist roll / pitch / yaw) are re-solved
(bounded least squares): lowest hand point at z = 0, hand xy and palm orientation kept close, small joint change.
Root, legs, waist and the other arm are NOT touched; the change fades out over --ramp frames.

Usage (gmr env): python arm_reach.py <clip_id> --src plantqp_vlm --out reachqp_vlm [--ramp 4] [--tol 0.005]"""
import argparse
import json
import os

import mujoco
import numpy as np
from scipy.optimize import least_squares
from scipy.spatial.transform import Rotation

from contact_lock import HAND_CAPSULE, HAND_R
from ground_fix import XML

H = os.path.expanduser("~")
ARM = ("shoulder_pitch", "shoulder_roll", "shoulder_yaw", "elbow", "wrist_roll", "wrist_pitch", "wrist_yaw")

ap = argparse.ArgumentParser()
ap.add_argument("clip_id")
ap.add_argument("--src", required=True)
ap.add_argument("--out", required=True)
ap.add_argument("--ramp", type=int, default=4)
ap.add_argument("--tol", type=float, default=0.005)
ap.add_argument("--w_xy", type=float, default=1.0, help="weight of keeping the hand xy (per m)")
a = ap.parse_args()
g = f"{H}/projects/dance/data/g1/{a.clip_id}"
csv = np.loadtxt(f"{g}/g1_{a.src}.csv", delimiter=",")
qpos = np.concatenate([csv[:, :3], csv[:, [6, 3, 4, 5]], csv[:, 7:]], 1)
T = len(qpos)
m = mujoco.MjModel.from_xml_path(XML)
d = mujoco.MjData(m)
ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
SIDES = ("left", "right")
planted = np.stack([np.array(ann.get(f"hand_{s}", [0] * T))[:T] == 1 for s in ("L", "R")], 1)
hb = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{s}_wrist_yaw_link") for s in SIDES]
jid = [[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{s}_{j}_joint") for j in ARM] for s in SIDES]
qadr = [[int(m.jnt_qposadr[i]) for i in js] for js in jid]


def hand(q, j):
  d.qpos[:] = q
  mujoco.mj_kinematics(m, d)
  p, R = d.xpos[hb[j]].copy(), d.xmat[hb[j]].reshape(3, 3).copy()
  pts = [p + R @ np.array(e) for e in HAND_CAPSULE[f"{SIDES[j]}_wrist_yaw_link"]]
  return min(x[2] for x in pts) - HAND_R, p, R


before = np.full((T, 2), np.nan)
after = np.full((T, 2), np.nan)
delta = np.zeros((T, 2, 7))
solved = np.zeros((T, 2), bool)
for t in range(T):
  for j in range(2):
    if not planted[t, j]:
      continue
    low, p0, R0 = hand(qpos[t], j)
    before[t, j] = low
    # every planted frame is solved (target z = 0, also lifts a penetrating hand), so the fade-out never pushes an
    # already planted hand into the floor
    lo, hi = m.jnt_range[jid[j], 0], m.jnt_range[jid[j], 1]
    x0 = qpos[t, qadr[j]]

    def res(x):
      q = qpos[t].copy()
      q[qadr[j]] = x
      lw, p, R = hand(q, j)
      return np.concatenate([[10 * lw], a.w_xy * (p[:2] - p0[:2]),
                             0.5 * (Rotation.from_matrix(R0).inv() * Rotation.from_matrix(R)).as_rotvec(),
                             0.05 * (x - x0)])
    x = least_squares(res, np.clip(x0, lo + 1e-6, hi - 1e-6), bounds=(lo, hi)).x
    delta[t, j] = x - x0
    solved[t, j] = True

out = qpos.copy()
for j in range(2):
  idx = np.where(solved[:, j])[0]
  if not len(idx):
    continue
  for t in range(T):
    if solved[t, j]:
      w = 1.0
      dl = delta[t, j]
    else:
      k = idx[np.abs(idx - t).argmin()]
      w = max(0.0, 1.0 - abs(t - k) / (a.ramp + 1))
      dl = delta[k, j]
    out[t, qadr[j]] = qpos[t, qadr[j]] + w * dl
for t in range(T):
  for j in range(2):
    if planted[t, j]:
      after[t, j] = hand(out[t], j)[0]
fixed = np.concatenate([out[:, :3], out[:, [4, 5, 6, 3]], out[:, 7:]], 1)
dst = f"{g}/g1_{a.out}.csv"
np.savetxt(dst, fixed.astype(np.float32), delimiter=",")
arm_ad = sum(qadr, [])
other = [i for i in range(m.nq) if i not in arm_ad]
rep = {"clip": a.clip_id, "src": a.src, "frames_solved(L,R)": solved.sum(0).tolist(),
       "planted_hand_z_cm mean before (L,R)": [round(float(np.nanmean(before[:, j]) * 100), 1) for j in range(2)],
       "planted_hand_z_cm mean after (L,R)": [round(float(np.nanmean(after[:, j]) * 100), 1) for j in range(2)],
       "planted_hand_z_cm max after (L,R)": [round(float(np.nanmax(after[:, j]) * 100), 1) for j in range(2)],
       "hand_min_z_cm_after": round(float(np.nanmin(after) * 100), 2),
       "arm_joint_change_rad_max (L,R)": [round(float(np.abs(delta[:, j]).max()), 3) for j in range(2)],
       "root_legs_waist_changed": bool(np.abs(out[:, other] - qpos[:, other]).max() > 0)}
json.dump(rep, open(dst.replace(".csv", ".json"), "w"), indent=1)
print(json.dumps(rep))
print("frame  hand L z cm before/after  hand R z cm before/after")
for t in np.where(planted.any(1))[0]:
  print(f"{t:4d}   " + "   ".join(f"{before[t, j] * 100:6.1f} / {after[t, j] * 100:5.1f}" if planted[t, j] else "      -       "
                                 for j in range(2)))
