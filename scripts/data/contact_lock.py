"""Generic (L0) contact repair of a retargeted G1 reference: every planted end-effector - feet AND hands - is put on
the floor and pinned horizontally while it is planted (any skill: walking, dancing, cartwheels, handsprings, ...).

Why: the monocular reconstruction floats / drifts vertically and has the wrong limb reach. cartwheel_1 (2026-10-25):
hands 0.15-0.35 m above the floor while the VLM labels them planted, feet 0.11-0.13 m up at the end. A pure root
shift (ground_fix.py) can only fix the lowest planted contact; when a hand and a foot are planted together their
gap is a pose error, which needs IK.

  1 root height offset: lowest planted contact point -> z = 0 (labels from data/annotations/<clip>.json:
    contact_L/R for the feet, hand_L/R for the hands), interpolated through unlabelled frames, smoothed, and
    clamped so that no foot or hand goes below the floor
  2 IK (mink), two passes: planted effectors -> pinned xy (median over the interval) and lowest point on the floor;
    free effectors keep their (interpolated) correction; pelvis / torso softly kept; posture regulariser
  Contact points: feet = lowest sole sphere of the ankle_roll link (GMR model); hands = lowest point of the
  hand collision capsule of mjlab's G1 (wrist_yaw link frame, fromto 0.07,0,0 -> 0.15,+-0.02,0, r 0.035).

Usage (gmr env): python contact_lock.py <clip_id> [--sigma 1.0] [--iters 30]
Writes data/g1/<clip>/g1_contact_vlm.csv (+ .json report)."""
import argparse
import json
import os

import mink
import mujoco
import numpy as np
from scipy.ndimage import gaussian_filter1d

H = os.path.expanduser("~")
XML = f"{H}/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"
EFF = ("left_ankle_roll_link", "right_ankle_roll_link", "left_wrist_yaw_link", "right_wrist_yaw_link")
HAND_CAPSULE = {"left_wrist_yaw_link": ((0.07, 0, 0), (0.15, -0.02, 0)),
                "right_wrist_yaw_link": ((0.07, 0, 0), (0.15, 0.02, 0))}
HAND_R = 0.035
KEEP = {"pelvis": (0.5, 2.0), "torso_link": (0.2, 3.0)}  # soft: the IK may lower the body to reach the floor


def segments(mask):
  out, s = [], None
  for t, m in enumerate(mask):
    if m and s is None:
      s = t
    if not m and s is not None:
      out.append((s, t - 1))
      s = None
  if s is not None:
    out.append((s, len(mask) - 1))
  return out


class Geo:
  def __init__(self, model):
    self.m, self.d = model, mujoco.MjData(model)
    self.bid = {n: mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, n) for n in EFF + tuple(KEEP)}
    self.spheres = {n: [g for g in range(model.ngeom) if model.geom_bodyid[g] == self.bid[n]
                        and model.geom_type[g] == mujoco.mjtGeom.mjGEOM_SPHERE] for n in EFF[:2]}

  def frame(self, q):
    """per effector: body position, rotation, lowest contact point z (world)."""
    self.d.qpos[:] = q
    mujoco.mj_kinematics(self.m, self.d)
    out = {}
    for n in EFF + tuple(KEEP):
      b = self.bid[n]
      p, Rm = self.d.xpos[b].copy(), self.d.xmat[b].reshape(3, 3).copy()
      low = None
      if n in self.spheres:
        low = min(self.d.geom_xpos[g, 2] - self.m.geom_size[g, 0] for g in self.spheres[n])
      elif n in HAND_CAPSULE:
        low = min((p + Rm @ np.array(e))[2] for e in HAND_CAPSULE[n]) - HAND_R
      out[n] = (p, Rm, low)
    return out


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("clip_id")
  ap.add_argument("--sigma", type=float, default=1.0)
  ap.add_argument("--iters", type=int, default=30)
  ap.add_argument("--ramp", type=float, default=10.0, help="frames over which a free effector's correction fades out")
  ap.add_argument("--smooth", type=float, default=5.0, help="pelvis continuity cost (target = previous solved frame)")
  ap.add_argument("--straight_support_arms", type=float, default=5.0,
                  help="family prior for hand-supported skills: elbow straight (q=1.277 on the G1) while that hand is "
                       "planted, cost weight (0 = off). cartwheel_1: the user saw a straight left arm in the video, "
                       "GVHMR gave 19-40 deg, GMR 36-48 deg, and the first contact lock bent the right elbow to 104 deg")
  a = ap.parse_args()
  g = f"{H}/projects/dance/data/g1/{a.clip_id}"
  csv = np.loadtxt(f"{g}/g1.csv", delimiter=",")
  qpos = np.concatenate([csv[:, :3], csv[:, [6, 3, 4, 5]], csv[:, 7:]], 1)
  T = len(qpos)
  model = mujoco.MjModel.from_xml_path(XML)
  geo = Geo(model)
  ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
  C = np.stack([np.array(ann["contact_L"][:T]) == 1, np.array(ann["contact_R"][:T]) == 1,
                np.array(ann.get("hand_L", [0] * T)[:T]) == 1, np.array(ann.get("hand_R", [0] * T)[:T]) == 1], 1)

  def lows(q):
    return np.array([[geo.frame(x)[n][2] for n in EFF] for x in q])

  low0 = lows(qpos)
  # 1 root height offset from the lowest planted FOOT (first version used hands too: the root jumped 20 cm when the
  #   support switched from a foot to the hands; reaching the floor with the hands is left to the IK)
  known = C[:, :2].any(1)
  off = np.full(T, np.nan)
  for t in np.where(known)[0]:
    off[t] = -low0[t, :2][C[t, :2]].min()
  idx = np.arange(T)
  off = np.interp(idx, idx[known], off[known]) if known.any() else np.zeros(T)
  off = gaussian_filter1d(off, a.sigma) if a.sigma > 0 else off
  off = np.maximum(off, -low0.min(1))  # nothing below the floor
  q1 = qpos.copy()
  q1[:, 2] += off

  out = q1.copy()
  lo, hi = model.jnt_range[1:, 0] + 1e-5, model.jnt_range[1:, 1] - 1e-5
  for _pass in range(2):
    F = [geo.frame(x) for x in out]
    P = np.array([[F[t][n][0] for n in EFF] for t in range(T)])
    L = np.array([[F[t][n][2] for n in EFF] for t in range(T)])
    corr = np.zeros((T, 4, 3))
    for j in range(4):
      kn = np.zeros(T, bool)
      for s, e in segments(C[:, j]):
        corr[s:e + 1, j, :2] = np.median(P[s:e + 1, j, :2], 0) - P[s:e + 1, j, :2]
        corr[s:e + 1, j, 2] = -L[s:e + 1, j]
        kn[s:e + 1] = True
      if kn.any():
        for k in range(3):
          corr[:, j, k] = np.interp(idx, idx[kn], corr[kn, j, k])
        # away from its contacts a free effector's correction fades to 0 over a.ramp frames (first version held it
        # constant: the raised arms of the standing pose were pulled down 0.37 m by the hand-support correction)
        dist = np.min(np.abs(idx[:, None] - idx[kn][None, :]), 1)
        corr[:, j] *= np.clip(1.0 - dist / a.ramp, 0.0, 1.0)[:, None]
        # a free effector may only be lifted by the interpolation, never pushed into the floor
        corr[:, j, 2] = np.maximum(corr[:, j, 2], -L[:, j])
    cfg = mink.Configuration(model)
    limits = [mink.ConfigurationLimit(model)]
    eff_tasks = [mink.FrameTask(n, "body", position_cost=30.0, orientation_cost=1.0, lm_damping=1) for n in EFF]
    keep_tasks = [mink.FrameTask(n, "body", position_cost=p, orientation_cost=o, lm_damping=1) for n, (p, o) in KEEP.items()]
    posture = mink.PostureTask(model, cost=0.05)
    # straight support arms: weight 1 while the hand is planted, fading over a.ramp frames around the contact
    arm_w = np.zeros((T, 2))
    for k, j in enumerate((2, 3)):
      kn = C[:, j]
      if kn.any():
        dist = np.min(np.abs(idx[:, None] - idx[kn][None, :]), 1)
        arm_w[:, k] = np.clip(1.0 - dist / a.ramp, 0.0, 1.0)
    elbow_dof = [6 + 18, 6 + 25]  # nv index of left / right elbow (free joint = 6 dofs)
    # effector task weight: 1 while planted, fading to 0 away from the contact (a free limb is not pinned in the world;
    # v2 pinned it and the free arms bent when the body moved, e.g. right elbow 0.8 -> 1.4 rad while standing)
    eff_w = np.zeros((T, 4))
    for j in range(4):
      kn = C[:, j]
      if kn.any():
        dist = np.min(np.abs(idx[:, None] - idx[kn][None, :]), 1)
        eff_w[:, j] = np.clip(1.0 - dist / a.ramp, 0.0, 1.0)
    # temporal continuity of the pelvis (v2: root height 0.32 -> 0.70 m in 4 frames at the first hand contact)
    smooth = mink.FrameTask("pelvis", "body", position_cost=a.smooth, orientation_cost=a.smooth / 5, lm_damping=1)
    new = out.copy()
    prev = None
    for t in range(T):
      q0 = out[t].copy()
      q0[7:] = np.clip(q0[7:], lo, hi)
      cfg.update(q0)
      posture.set_target(q0)
      for j, task in enumerate(eff_tasks):
        task.set_position_cost(30.0 * eff_w[t, j])
        task.set_orientation_cost(1.0 * eff_w[t, j])
      tasks = [tk for j, tk in enumerate(eff_tasks) if eff_w[t, j] > 0] + keep_tasks + [posture]
      if prev is not None and a.smooth > 0:
        smooth.set_target(prev)
        tasks = tasks + [smooth]
      if a.straight_support_arms > 0 and arm_w[t].any():
        cost = np.zeros(model.nv)
        qs = q0.copy()
        for k, dof in enumerate(elbow_dof):
          cost[dof] = a.straight_support_arms * arm_w[t, k]
          qs[7 + (18 if k == 0 else 25)] = 1.277
        arm_task = mink.PostureTask(model, cost=cost)
        arm_task.set_target(qs)
        tasks = tasks + [arm_task]
      for j, (task, n) in enumerate(zip(eff_tasks, EFF)):
        p, Rm, _ = F[t][n]
        task.set_target(mink.SE3.from_rotation_and_translation(mink.SO3.from_matrix(Rm), p + corr[t, j]))
      for task, n in zip(keep_tasks, KEEP):
        p, Rm, _ = F[t][n]
        task.set_target(mink.SE3.from_rotation_and_translation(mink.SO3.from_matrix(Rm), p))
      for _ in range(a.iters):
        vel = mink.solve_ik(cfg, tasks, 0.01, "daqp", 1e-2, limits)
        cfg.integrate_inplace(vel, 0.01)
        q = cfg.q.copy()
        q[7:] = np.clip(q[7:], lo, hi)
        cfg.update(q)
      new[t] = cfg.q.copy()
      prev = cfg.get_transform_frame_to_world("pelvis", "body")
    out = new
  low2 = lows(out)
  fixed = np.concatenate([out[:, :3], out[:, [4, 5, 6, 3]], out[:, 7:]], 1)
  dst = f"{g}/g1_contact_vlm.csv"
  np.savetxt(dst, fixed.astype(np.float32), delimiter=",")

  def planted_err(lw):
    return {n: (round(float(np.abs(lw[C[:, j], j]).mean() * 100), 1) if C[:, j].any() else None)
            for j, n in enumerate(("foot_L", "foot_R", "hand_L", "hand_R"))}
  rep = {"clip": a.clip_id, "frames": T, "root_offset_cm": [round(float(off.min() * 100), 1), round(float(off.max() * 100), 1)],
         "planted_contact_height_cm_mean before": planted_err(low0), "after": planted_err(low2),
         "penetration_cm_min_after": round(float(low2.min() * 100), 1),
         "joint_change_rad_max": round(float(np.abs(out[:, 7:] - qpos[:, 7:]).max()), 3),
         "pelvis_shift_cm_max": round(float(np.linalg.norm(out[:, :3] - qpos[:, :3], axis=1).max() * 100), 1)}
  json.dump(rep, open(dst.replace(".csv", ".json"), "w"), indent=1)
  print(json.dumps(rep))


if __name__ == "__main__":
  main()
