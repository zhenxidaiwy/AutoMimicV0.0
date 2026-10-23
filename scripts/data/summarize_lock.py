"""Aggregate ground-fix / foot-lock reports over all clips: VLM contacts vs speed-heuristic contacts.
Usage (gmr env): python summarize_lock.py   -> prints a markdown table and writes ~/dance_win/results/foot_lock_summary.md
"""
import glob
import json
import os

import numpy as np

if __name__ == "__main__":
    H = os.path.expanduser("~")
    rows = []
    for d in sorted(glob.glob(f"{H}/projects/dance/data/g1/*/")):
        cid = os.path.basename(d.rstrip("/"))
        try:
            v = json.load(open(f"{d}/g1_lock_vlm.json"))
            h = json.load(open(f"{d}/g1_lock_heuristic.json"))
            g = json.load(open(f"{d}/g1_ground_vlm.json"))
        except FileNotFoundError:
            continue
        key_b, key_a = "planted_foot_speed_mps(mean,p95) before", "planted_foot_speed_mps(mean,p95) after"
        rows.append((cid, v["frames"], v[key_b][0], v[key_a][0], h[key_a][0], g["heuristic_vs_vlm_contact_agreement"],
                     g["before"]["planted_sole_z_mean_cm"], g["after"]["planted_sole_z_mean_cm"]))
    lines = ["| 片段 | 帧数 | 修正前打滑 | VLM 锁脚后 | 启发式锁脚后 | 启发式与 VLM 触地一致率 | 踩地脚离地 前→后 (cm) |",
             "|---|---|---|---|---|---|---|"]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]:.3f} | {r[3]:.3f} | {r[4]:.3f} | {r[5]:.2f} | {r[6]:.1f} → {r[7]:.1f} |")
    a = np.array([r[1:] for r in rows], float)
    w = a[:, 0] / a[:, 0].sum()
    lines.append(f"| **加权平均（按帧数）** | {int(a[:, 0].sum())} | {(a[:, 1] * w).sum():.3f} | {(a[:, 2] * w).sum():.3f} | "
                 f"{(a[:, 3] * w).sum():.3f} | {(a[:, 4] * w).sum():.2f} | {(a[:, 5] * w).sum():.1f} → {(a[:, 6] * w).sum():.1f} |")
    lines.append(f"\n打滑 = 按 VLM 标注为踩地的帧上，脚的平均水平速度 (m/s)。共 {len(rows)} 个片段。")
    out = "\n".join(lines)
    print(out)
    os.makedirs(f"{H}/dance_win/results", exist_ok=True)
    open(f"{H}/dance_win/results/foot_lock_summary.md", "w", encoding="utf-8").write(out + "\n")
