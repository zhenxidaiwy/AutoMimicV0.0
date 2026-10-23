"""Contact-aware vertical grounding of a retargeted G1 motion.

Monocular reconstruction leaves the whole body floating / drifting vertically (G1 ankle should sit at ~0.035 m when
the sole is flat; raw clips show 0.07-0.13 m while standing). Given per-frame contact labels, we shift the root
height so that the lowest sole point of the planted foot (or the lower of two planted feet) touches z=0.
Frames without a reliable label get the offset linearly interpolated, then the offset is lightly smoothed.

Contact sources (ablation):
  vlm        labels from data/annotations/<clip>.json (VLM, 1 planted / 0 air / -1 unsure)
  heuristic  foot horizontal speed < 0.25 m/s  (no VLM; typical kinematic baseline)

Usage (gmr env): python ground_fix.py <clip_id> [--contacts vlm|heuristic] [--sigma 1.5]
Writes data/g1/<clip>/g1_ground_<src>.csv (+ .json report)
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
    a = ap.parse_args()
    g = f"{H}/projects/dance/data/g1/{a.clip_id}"
    csv = np.loadtxt(f"{g}/g1.csv", delimiter=",")
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

    known = (contact == 1).any(axis=1)
    off = np.full(T, np.nan)
    for t in np.where(known)[0]:
        off[t] = -sole[t][contact[t] == 1].min()
    idx = np.arange(T)
    off = np.interp(idx, idx[known], off[known]) if known.any() else np.zeros(T)
    off = gaussian_filter1d(off, a.sigma) if a.sigma > 0 else off
    # hard constraint for both contact sources: no sole point below the floor
    floor_clamp = -sole.min(axis=1)
    clamped = off < floor_clamp - 0.002  # count only real conflicts (>2 mm), not smoothing noise
    off = np.maximum(off, floor_clamp)

    fixed = csv.copy()
    fixed[:, 2] += off
    out = f"{g}/g1_ground_{a.contacts}.csv"
    np.savetxt(out, fixed.astype(np.float32), delimiter=",")
    sole_after = sole + off[:, None]
    # evaluate against the VLM labels in both cases (they are the reference annotation)
    ann_eval = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
    c_eval = np.stack([ann_eval["contact_L"], ann_eval["contact_R"]], 1)[:T]
    rep = {"clip": a.clip_id, "contacts": a.contacts, "frames": T,
           "root_offset_cm": {"mean": round(float(off.mean() * 100), 2), "min": round(float(off.min() * 100), 2),
                              "max": round(float(off.max() * 100), 2)},
           "frames_clamped_by_no_penetration": int(clamped.sum()),
           "before": float_stats(sole, c_eval), "after": float_stats(sole_after, c_eval),
           "planted_foot_speed_mps_mean(vlm labels)": round(float(speed[c_eval == 1].mean()), 3),
           "heuristic_vs_vlm_contact_agreement": round(float(((speed < 0.25).astype(int) == c_eval)[c_eval >= 0].mean()), 3)}
    json.dump(rep, open(out.replace(".csv", ".json"), "w"), indent=1)
    print(json.dumps(rep, ensure_ascii=False))
