"""Per-frame 2D ankle height (pixels above the lowest ankle position) from GVHMR's ViTPose output.

Static camera only: a planted foot sits at its lowest image y and does not move.
Usage (gmr env): python ankle2d.py <clip_id> [--start 0 --end -1 --step 1]
Prints: frame, image-left/right ankle lift (px), conf, and performer-side labels (COCO: 15=left ankle, 16=right ankle).
"""
import argparse
import os

import numpy as np
import torch

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=-1)
    ap.add_argument("--step", type=int, default=1)
    a = ap.parse_args()
    D = os.path.expanduser("~/projects/dance/data")
    kp = torch.load(f"{D}/gvhmr/{a.clip_id}/preprocess/vitpose.pt", weights_only=False).numpy()  # (T,17,3) x,y,conf
    T = len(kp)
    end = T if a.end < 0 else min(a.end, T)
    la, ra = kp[:, 15], kp[:, 16]  # performer's left / right ankle
    scale = np.median(np.linalg.norm(kp[:, 11, :2] - kp[:, 15, :2], axis=1))  # hip-ankle length (px) for normalising
    floor_l, floor_r = np.percentile(la[:, 1], 95), np.percentile(ra[:, 1], 95)
    print(f"T={T} leg_len_px={scale:.1f}  lift = (floor_y - ankle_y)/leg_len*100 (% leg length); v = |d xy|/leg_len*100 per frame")
    print("frame  L_lift  L_v   R_lift  R_v   L_conf R_conf")
    for t in range(a.start, end, a.step):
        lv = np.linalg.norm(la[t, :2] - la[max(t - 1, 0), :2]) / scale * 100
        rv = np.linalg.norm(ra[t, :2] - ra[max(t - 1, 0), :2]) / scale * 100
        print(f"{t:5d}  {(floor_l - la[t,1]) / scale * 100:6.1f} {lv:5.1f}  {(floor_r - ra[t,1]) / scale * 100:6.1f} {rv:5.1f}"
              f"  {la[t,2]:.2f}   {ra[t,2]:.2f}")
