"""Contact-aware horizontal foot locking (removes foot skating) on a ground-fixed G1 motion, via mink IK.

For every contiguous planted interval of a foot, the foot is pinned to the median xy it had over that interval.
The resulting per-frame xy correction is linearly interpolated through swing frames (no jumps at boundaries).
Each frame is then re-solved with IK: feet -> corrected targets (high weight), pelvis / torso / wrists -> original
poses, posture regulariser -> original joints.

Usage (gmr env): python foot_lock.py <clip_id> [--contacts vlm|heuristic]
Input : data/g1/<clip>/g1_ground_<contacts>.csv     Output: data/g1/<clip>/g1_lock_<contacts>.csv (+ .json report)
The report always evaluates against the VLM labels (the reference annotation).
"""
import argparse
import json
import os

import mink
import mujoco
import numpy as np

H = os.path.expanduser("~")
XML = f"{H}/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"
FEET = ("left_ankle_roll_link", "right_ankle_roll_link")
KEEP = {"pelvis": (5.0, 5.0), "torso_link": (1.0, 5.0), "left_wrist_yaw_link": (2.0, 0.0),
        "right_wrist_yaw_link": (2.0, 0.0)}


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


def fk_poses(model, qpos, names):
    data = mujoco.MjData(model)
    ids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, n) for n in names]
    pos = np.zeros((len(qpos), len(names), 3))
    rot = np.zeros((len(qpos), len(names), 3, 3))
    for t, q in enumerate(qpos):
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        pos[t] = data.xpos[ids]
        rot[t] = data.xmat[ids].reshape(-1, 3, 3)
    return pos, rot


def planted_speed(pos_feet, contact, fps=30):
    v = np.zeros(contact.shape)
    v[1:] = np.linalg.norm(np.diff(pos_feet[..., :2], axis=0), axis=-1) * fps
    m = contact == 1
    return round(float(v[m].mean()), 4), round(float(np.percentile(v[m], 95)), 4)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--contacts", default="vlm", choices=["vlm", "heuristic"])
    ap.add_argument("--iters", type=int, default=20)
    a = ap.parse_args()
    g = f"{H}/projects/dance/data/g1/{a.clip_id}"
    csv = np.loadtxt(f"{g}/g1_ground_{a.contacts}.csv", delimiter=",")
    qpos = np.concatenate([csv[:, :3], csv[:, [6, 3, 4, 5]], csv[:, 7:]], 1)
    T = len(qpos)
    model = mujoco.MjModel.from_xml_path(XML)
    names = list(FEET) + list(KEEP)
    pos, rot = fk_poses(model, qpos, names)

    ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
    c_vlm = np.stack([ann["contact_L"], ann["contact_R"]], 1)[:T]
    if a.contacts == "vlm":
        contact = c_vlm
    else:
        v = np.zeros((T, 2))
        v[1:] = np.linalg.norm(np.diff(pos[:, :2, :2], axis=0), axis=-1) * 30
        contact = (v < 0.25).astype(int)

    # per-foot xy correction: pin planted intervals to their median xy, interpolate between intervals
    corr = np.zeros((T, 2, 2))
    for j in range(2):
        known = np.zeros(T, bool)
        for s, e in segments(contact[:, j] == 1):
            corr[s:e + 1, j] = np.median(pos[s:e + 1, j, :2], axis=0) - pos[s:e + 1, j, :2]
            known[s:e + 1] = True
        if known.any():
            for k in range(2):
                corr[:, j, k] = np.interp(np.arange(T), np.where(known)[0], corr[known, j, k])

    cfg = mink.Configuration(model)
    limits = [mink.ConfigurationLimit(model)]
    foot_tasks = [mink.FrameTask(f, "body", position_cost=30.0, orientation_cost=3.0, lm_damping=1) for f in FEET]
    keep_tasks = [mink.FrameTask(n, "body", position_cost=p, orientation_cost=o, lm_damping=1) for n, (p, o) in KEEP.items()]
    posture = mink.PostureTask(model, cost=0.05)
    tasks = foot_tasks + keep_tasks + [posture]
    out = np.zeros_like(qpos)
    dt = 0.01
    lo, hi = model.jnt_range[1:, 0] + 1e-5, model.jnt_range[1:, 1] - 1e-5
    qpos[:, 7:] = np.clip(qpos[:, 7:], lo, hi)  # float32 csv rounding can put a joint 1e-6 past its limit
    for t in range(T):
        cfg.update(qpos[t])
        posture.set_target(qpos[t])
        for j, task in enumerate(foot_tasks):
            p = pos[t, j].copy()
            p[:2] += corr[t, j]
            task.set_target(mink.SE3.from_rotation_and_translation(mink.SO3.from_matrix(rot[t, j]), p))
        for k, task in enumerate(keep_tasks):
            task.set_target(mink.SE3.from_rotation_and_translation(mink.SO3.from_matrix(rot[t, 2 + k]), pos[t, 2 + k]))
        for _ in range(a.iters):
            vel = mink.solve_ik(cfg, tasks, dt, "daqp", 1e-2, limits)
            cfg.integrate_inplace(vel, dt)
            q = cfg.q.copy()  # integration can overshoot a limit by ~1e-7 and the next solve then raises
            q[7:] = np.clip(q[7:], lo, hi)
            cfg.update(q)
        out[t] = cfg.q.copy()

    pos_new, _ = fk_poses(model, out, names)
    fixed = np.concatenate([out[:, :3], out[:, [4, 5, 6, 3]], out[:, 7:]], 1)
    dst = f"{g}/g1_lock_{a.contacts}.csv"
    np.savetxt(dst, fixed.astype(np.float32), delimiter=",")
    rep = {"clip": a.clip_id, "contacts": a.contacts, "frames": T,
           "planted_foot_speed_mps(mean,p95) before": planted_speed(pos[:, :2], c_vlm),
           "planted_foot_speed_mps(mean,p95) after": planted_speed(pos_new[:, :2], c_vlm),
           "foot_target_err_cm_max": round(float(np.abs(pos_new[:, :2, :2] - (pos[:, :2, :2] + corr)).max() * 100), 2),
           "pelvis_shift_cm_max": round(float(np.linalg.norm(pos_new[:, 2] - pos[:, 2], axis=-1).max() * 100), 2),
           "joint_change_rad_max": round(float(np.abs(out[:, 7:] - qpos[:, 7:]).max()), 3),
           "min_sole_proxy_ankle_z": round(float(pos_new[:, :2, 2].min()), 4)}
    json.dump(rep, open(dst.replace(".csv", ".json"), "w"), indent=1)
    print(json.dumps(rep))
