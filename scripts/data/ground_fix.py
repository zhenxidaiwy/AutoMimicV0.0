"""Contact-aware vertical grounding of a retargeted G1 motion.

Monocular reconstruction leaves the whole body floating / drifting vertically (G1 ankle should sit at ~0.035 m when
the sole is flat; raw clips show 0.07-0.13 m while standing). Given per-frame contact labels, we shift the root
height so that the lowest sole point of the planted foot (or the lower of two planted feet) touches z=0.
Frames without a reliable label get the offset linearly interpolated, then the offset is lightly smoothed.

Contact sources (ablation):
  vlm        labels from data/annotations/<clip>.json (VLM, 1 planted / 0 air / -1 unsure)
  heuristic  foot horizontal speed < 0.25 m/s  (no VLM; typical kinematic baseline)

Usage (gmr env): python ground_fix.py <clip_id> [--contacts vlm|heuristic] [--sigma 1.5] [--qp W] [--out ground]
Writes data/g1/<clip>/g1_<out>_<contacts>.csv (+ .json report)
"""
import argparse
import json
import os

import mujoco
import numpy as np
from scipy.ndimage import gaussian_filter1d

H = os.path.expanduser("~")
XML = f"{H}/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"
FEET = ("left_ankle_roll_link", "right_ankle_roll_link")


def sole_heights(model, qpos):
    """Lowest sole-sphere point (z - radius) per foot per frame, plus foot xy (ankle) for speed."""
    data = mujoco.MjData(model)
    bids = [mujoco.mj_name2id(model, mujoco.mjtObj.mjOBJ_BODY, b) for b in FEET]
    geoms = [[g for g in range(model.ngeom) if model.geom_bodyid[g] == b and model.geom_type[g] == mujoco.mjtGeom.mjGEOM_SPHERE]
             for b in bids]
    sole = np.zeros((len(qpos), 2))
    xy = np.zeros((len(qpos), 2, 2))
    for t, q in enumerate(qpos):
        data.qpos[:] = q
        mujoco.mj_kinematics(model, data)
        for j, gs in enumerate(geoms):
            sole[t, j] = min(data.geom_xpos[g, 2] - model.geom_size[g, 0] for g in gs)
            xy[t, j] = data.xpos[bids[j], :2]
    return sole, xy


def float_stats(sole, contact):
    planted = contact == 1
    h = sole[planted]
    return {"planted_sole_z_mean_cm": round(float(h.mean() * 100), 2) if h.size else None,
            "planted_sole_z_abs_p95_cm": round(float(np.percentile(np.abs(h), 95) * 100), 2) if h.size else None,
            "penetration_frames(<-1cm)": int((sole < -0.01).any(axis=1).sum())}


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--contacts", default="vlm", choices=["vlm", "heuristic"])
    ap.add_argument("--sigma", type=float, default=1.5)
    ap.add_argument("--hands", action="store_true",
                    help="also ground the planted HANDS (hand_L/R labels; lowest point of the hand collision capsule): "
                         "hand-supported skills. cartwheel_2: the palms are on the floor in the GVHMR result but the G1 "
                         "hands stayed 4-12 cm up (G1 arms are scaled 0.8 vs legs 0.9). Root height only, no joint change")
    ap.add_argument("--src", default="g1", help="input csv stem in data/g1/<clip>/ (default g1)")
    ap.add_argument("--qp", type=float, default=0.0,
                    help="> 0: root offset = bounded least squares (planted contacts on the floor, NO point below it) "
                         "+ this weight x its second difference (vertical acceleration). cartwheel_2: the per-frame "
                         "offset switched from the foot to the hand when the foot lifted -> root -7 cm in 2 frames "
                         "(-21.5 m/s^2, ~2 g down with a foot on the floor), the reference got infeasible there")
    ap.add_argument("--out", default="ground", help="output stem: g1_<out>_<contacts>.csv")
    a = ap.parse_args()
    g = f"{H}/projects/dance/data/g1/{a.clip_id}"
    csv = np.loadtxt(f"{g}/{a.src}.csv", delimiter=",")
    qpos = np.concatenate([csv[:, :3], csv[:, [6, 3, 4, 5]], csv[:, 7:]], 1)  # csv quat xyzw -> mujoco wxyz
    model = mujoco.MjModel.from_xml_path(XML)
    sole, xy = sole_heights(model, qpos)
    T = len(qpos)

    speed = np.zeros((T, 2))
    speed[1:] = np.linalg.norm(np.diff(xy, axis=0), axis=-1) * 30
    if a.contacts == "vlm":
        ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
        contact = np.stack([ann["contact_L"], ann["contact_R"]], 1)[:T]
    else:
        contact = (speed < 0.25).astype(int)

    if a.hands:  # hand contacts as two more "feet": lowest hand-capsule point, labels hand_L / hand_R
        import sys as _sys
        _sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
        from contact_lock import EFF, Geo
        geo = Geo(model)
        hand_low = np.array([[geo.frame(q)[n][2] for n in EFF[2:]] for q in qpos])
        ann_h = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
        hand_c = np.stack([ann_h.get("hand_L", [0] * T), ann_h.get("hand_R", [0] * T)], 1)[:T]
        sole = np.concatenate([sole, hand_low], 1)
        contact = np.concatenate([contact, hand_c], 1)
    known = (contact == 1).any(axis=1)
    off = np.full(T, np.nan)
    for t in np.where(known)[0]:
        off[t] = -sole[t][contact[t] == 1].min()
    idx = np.arange(T)
    off = np.interp(idx, idx[known], off[known]) if known.any() else np.zeros(T)
    off = gaussian_filter1d(off, a.sigma) if a.sigma > 0 else off
    # hard constraint for both contact sources: no sole point below the floor
    floor_clamp = -sole.min(axis=1)
    if a.qp > 0:
        from scipy.optimize import lsq_linear
        from scipy.sparse import diags, eye, vstack
        tgt = np.full(T, np.nan)
        for t in np.where(known)[0]:
            tgt[t] = -sole[t][contact[t] == 1].min()
        w = np.where(known, 1.0, 0.0)
        tgt = np.where(known, tgt, 0.0)
        D2 = diags([1.0, -2.0, 1.0], [0, 1, 2], shape=(T - 2, T))
        A = vstack([diags(w), np.sqrt(a.qp) * D2]).tocsr()
        rhs = np.concatenate([w * tgt, np.zeros(T - 2)])
        off = lsq_linear(A, rhs, bounds=(floor_clamp, np.full(T, np.inf)), lsmr_tol="auto").x
    clamped = off < floor_clamp - 0.002  # count only real conflicts (>2 mm), not smoothing noise
    off = np.maximum(off, floor_clamp)

    fixed = csv.copy()
    fixed[:, 2] += off
    out = f"{g}/g1_{a.out}_{a.contacts}.csv"
    np.savetxt(out, fixed.astype(np.float32), delimiter=",")
    sole_after = sole + off[:, None]
    # evaluate against the VLM labels in both cases (they are the reference annotation)
    ann_eval = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
    c_eval = np.stack([ann_eval["contact_L"], ann_eval["contact_R"]], 1)[:T]
    rep = {"clip": a.clip_id, "contacts": a.contacts, "frames": T,
           "root_offset_cm": {"mean": round(float(off.mean() * 100), 2), "min": round(float(off.min() * 100), 2),
                              "max": round(float(off.max() * 100), 2)},
           "frames_clamped_by_no_penetration": int(clamped.sum()),
           "before": float_stats(sole[:, :2], c_eval), "after": float_stats(sole_after[:, :2], c_eval),
           **({"hands_planted_z_cm_mean before/after": [
               round(float(sole[:, 2:][contact[:, 2:] == 1].mean() * 100), 1),
               round(float(sole_after[:, 2:][contact[:, 2:] == 1].mean() * 100), 1)]} if a.hands else {}),
           "root_az_max_abs_mps2 before/after": [round(float(np.abs(np.gradient(np.gradient(csv[:, 2], 1 / 30), 1 / 30)).max()), 1),
                                                 round(float(np.abs(np.gradient(np.gradient(fixed[:, 2], 1 / 30), 1 / 30)).max()), 1)],
           "planted_contact_z_cm_max": round(float(np.where(contact == 1, sole_after, -np.inf).max() * 100), 2),
           "planted_foot_speed_mps_mean(vlm labels)": round(float(speed[c_eval == 1].mean()), 3),
           "heuristic_vs_vlm_contact_agreement": round(float(((speed < 0.25).astype(int) == c_eval)[c_eval >= 0].mean()), 3)}
    json.dump(rep, open(out.replace(".csv", ".json"), "w"), indent=1)
    print(json.dumps(rep, ensure_ascii=False))
