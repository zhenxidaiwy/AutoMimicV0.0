"""Propose swing intervals from ViTPose 2D ankles (static camera) for the VLM annotator to verify / edit.

A foot is proposed 'in swing' when its image speed > v_thr % leg length per frame OR it is lifted > lift_thr % above its
local floor (rolling 95th-percentile of image y over +-1 s, robust to slow drift toward/away from the camera).
Low-confidence frames (< 0.6) are marked unsure. Short gaps (<= 2 frames) are merged; swings shorter than 3 frames dropped.
Usage (gmr env): python propose_swings.py <clip_id> [--v_thr 4] [--lift_thr 7]
"""
import argparse
import json
import os

import numpy as np
import torch
from scipy.ndimage import maximum_filter1d, percentile_filter


def runs(mask, min_len=3, max_gap=2):
    m = mask.copy()
    idx = np.where(m)[0]
    for a, b in zip(idx[:-1], idx[1:]):  # close small gaps
        if 1 < b - a <= max_gap + 1:
            m[a:b] = True
    out, s = [], None
    for t, v in enumerate(m):
        if v and s is None:
            s = t
        if not v and s is not None:
            if t - s >= min_len:
                out.append([s, t - 1])
            s = None
    if s is not None and len(m) - s >= min_len:
        out.append([s, len(m) - 1])
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--v_thr", type=float, default=4.0)
    ap.add_argument("--lift_thr", type=float, default=7.0)
    a = ap.parse_args()
    kp = torch.load(os.path.expanduser(f"~/projects/dance/data/gvhmr/{a.clip_id}/preprocess/vitpose.pt"),
                    weights_only=False).numpy()
    T = len(kp)
    leg = np.median(np.linalg.norm(kp[:, 11, :2] - kp[:, 15, :2], axis=1))
    out = {"T": T, "swing": [], "unsure": []}
    conf_bad = np.zeros(T, bool)
    for side, j in (("L", 15), ("R", 16)):
        y, xy, c = kp[:, j, 1], kp[:, j, :2], kp[:, j, 2]
        floor = percentile_filter(y, 95, size=61, mode="nearest")
        lift = (floor - y) / leg * 100
        v = np.r_[0, np.linalg.norm(np.diff(xy, axis=0), axis=1)] / leg * 100
        v = maximum_filter1d(v, 3)
        swing = (v > a.v_thr) | (lift > a.lift_thr)
        conf_bad |= c < 0.6
        for s, e in runs(swing):
            out["swing"].append([s, e, side])
    out["unsure"] = runs(conf_bad, min_len=1, max_gap=1)
    both = np.zeros(T, int)
    for s, e, _ in out["swing"]:
        both[s:e + 1] += 1
    out["both_in_swing_frames"] = runs(both >= 2, min_len=1, max_gap=0)
    print(json.dumps(out))
