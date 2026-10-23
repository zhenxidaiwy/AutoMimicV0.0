"""Package processed clips into a G1 imitation dataset and report VLM-vs-kinematic contact agreement.

Usage (gmr env): python build_dataset.py
Reads  ~/dance_win/data/annotations/clips.tsv, ~/projects/dance/data/{g1,gvhmr}/<clip>/, annotations/<clip>.json
Writes ~/projects/dance/dataset/<clip>/ and ~/projects/dance/dataset/manifest.json (+ copy of manifest to dance_win)

Per clip:
  g1_30fps.csv        root pos(3) + root quat xyzw(4) + 29 joint angles, 30 fps (BeyondMimic/unitree csv format)
  g1_50fps.npz        mjlab tracking format (joint_pos/vel, body_pos/quat/lin_vel/ang_vel_w), 50 fps
  smplx_world.npz     GVHMR world-frame SMPL-X params (global_orient, body_pose, transl, betas), 30 fps
  annotation.json     VLM labels: phases, per-frame contact_L/R, rsi_weight (30 fps)
  labels_50fps.npz    the same labels resampled to the 50 fps npz timeline (nearest frame)
  metrics.json        retarget QA metrics
"""
import json
import os
import shutil

import numpy as np
import torch

H = os.path.expanduser("~")
D, OUT, ANN = f"{H}/projects/dance/data", f"{H}/projects/dance/dataset", f"{H}/dance_win/data/annotations"
PHASES = ["ready", "stand", "prep", "flash", "hold", "recover", "settle", "shake", "other"]


def kin_contact(feet, fps, h_thr=0.03, v_thr=0.25):
    """Kinematic contact from robot ankle trajectory: within h_thr of the floor and slower than v_thr m/s."""
    z = feet[..., 2]
    floor = np.percentile(z.min(axis=1), 5)
    v = np.zeros(z.shape)
    v[1:] = np.linalg.norm(np.diff(feet[..., :2], axis=0), axis=-1) * fps
    return (((z - floor) < h_thr) & (v < v_thr)).astype(int)  # (T, 2) [L, R]


def agreement(ann, kin):
    out = {}
    for j, side in enumerate("LR"):
        lab = np.array(ann[f"contact_{side}"])
        n = min(len(lab), len(kin))
        lab, k = lab[:n], kin[:n, j]
        m = lab >= 0
        out[side] = {"frames_labeled": int(m.sum()), "agree": round(float((lab[m] == k[m]).mean()), 3),
                     "vlm_contact_but_kin_air": int(((lab == 1) & (k == 0) & m).sum()),
                     "vlm_air_but_kin_contact": int(((lab == 0) & (k == 1) & m).sum())}
    return out


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    rows = [l.rstrip("\n").split("\t") for l in open(f"{ANN}/clips.tsv", encoding="utf-8") if l.strip() and not l.startswith("#")]
    manifest = []
    for raw, cid, ss, to, cam, move, perf, note in rows:
        g = f"{D}/g1/{cid}"
        if not os.path.exists(f"{g}/g1.csv"):
            print(f"[pending] {cid}")
            continue
        o = f"{OUT}/{cid}"
        os.makedirs(o, exist_ok=True)
        shutil.copy(f"{g}/g1.csv", f"{o}/g1_30fps.csv")
        has_npz = os.path.exists(f"{g}/g1_50fps.npz")
        if has_npz:
            shutil.copy(f"{g}/g1_50fps.npz", f"{o}/g1_50fps.npz")
        ground = {}
        for v in ("ground_vlm", "ground_heuristic", "lock_vlm", "lock_heuristic"):
            for ext in (".csv", "_50fps.npz", ".json"):
                src = f"{g}/g1_{v}{ext}"
                if os.path.exists(src):
                    shutil.copy(src, f"{o}/g1_{v}{ext}")
            if os.path.exists(f"{g}/g1_{v}.json"):
                ground[v] = json.load(open(f"{g}/g1_{v}.json"))
        pred = torch.load(f"{D}/gvhmr/{cid}/hmr4d_results.pt", weights_only=False)["smpl_params_global"]
        np.savez(f"{o}/smplx_world.npz", fps=30, **{k: v.numpy() for k, v in pred.items()})
        metrics = json.load(open(f"{g}/metrics.json"))
        json.dump(metrics, open(f"{o}/metrics.json", "w"), indent=1)
        entry = {"clip_id": cid, "move": move, "performer": perf, "source": f"bilibili {raw} {ss}-{to}s",
                 "camera": cam, "frames_30fps": metrics["frames"], "seconds": metrics["seconds"],
                 "has_npz_50fps": has_npz, "annotated": False, "note": note,
                 "retarget_qa": {k: metrics[k] for k in ("foot_slide_mps_in_contact_mean", "joint_limit_violation_max_rad",
                                                          "root_z_min", "human_height_est_m")}}
        ap = f"{ANN}/{cid}.json"
        if os.path.exists(ap):
            ann = json.load(open(ap, encoding="utf-8"))
            shutil.copy(ap, f"{o}/annotation.json")
            T30 = len(ann["phase"])
            if has_npz:
                T50 = len(np.load(f"{g}/g1_50fps.npz")["joint_pos"])
                idx = np.minimum(np.round(np.arange(T50) * 30 / 50).astype(int), T30 - 1)
                w = np.array(ann["rsi_weight"])[idx]
                np.savez(f"{o}/labels_50fps.npz", phase=np.array([PHASES.index(ann["phase"][i]) for i in idx]),
                         phase_names=np.array(PHASES), contact_L=np.array(ann["contact_L"])[idx],
                         contact_R=np.array(ann["contact_R"])[idx], rsi_weight=w / w.sum())
            kin = kin_contact(np.load(f"{g}/feet_xyz.npy"), metrics["fps"])
            entry["annotated"] = True
            entry["quality"] = ann.get("quality")
            if ann.get("duplicate_of"):
                entry["duplicate_of"] = ann["duplicate_of"]
            entry["contact_agreement_vlm_vs_kinematic"] = agreement(ann, kin)
        gfix = {v: r for v, r in ground.items() if v.startswith("ground")}
        lock = {v: r for v, r in ground.items() if v.startswith("lock")}
        if gfix:
            entry["ground_fix"] = {v: {"after": r["after"], "root_offset_cm": r["root_offset_cm"]} for v, r in gfix.items()}
            entry["ground_fix"]["before"] = next(iter(gfix.values()))["before"]
            entry["heuristic_vs_vlm_contact_agreement"] = next(iter(gfix.values()))["heuristic_vs_vlm_contact_agreement"]
        if lock:
            entry["foot_lock"] = {v: {k: r[k] for k in r if k not in ("clip", "contacts", "frames")} for v, r in lock.items()}
        manifest.append(entry)
        print(f"[ok] {cid}: {entry['seconds']}s npz={has_npz} annotated={entry['annotated']}"
              + (f" agree L/R={entry['contact_agreement_vlm_vs_kinematic']['L']['agree']}/"
                 f"{entry['contact_agreement_vlm_vs_kinematic']['R']['agree']}" if entry["annotated"] else ""))
    json.dump(manifest, open(f"{OUT}/manifest.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    shutil.copy(f"{OUT}/manifest.json", f"{H}/dance_win/data/manifest.json")
    uniq = [e for e in manifest if not e.get("duplicate_of")]
    by_move = {}
    for e in uniq:
        by_move.setdefault(e["move"], []).append(e["seconds"])
    print(f"dataset: {len(manifest)} clips ({len(uniq)} unique), unique {sum(e['seconds'] for e in uniq):.1f}s, "
          f"annotated {sum(e['annotated'] for e in manifest)} | " +
          ", ".join(f"{m}: {len(v)} clips {sum(v):.1f}s" for m, v in by_move.items()))
