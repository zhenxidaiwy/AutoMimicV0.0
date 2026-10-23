"""Detect hard cuts / jump cuts in a clip from consecutive-frame differences.

A cut shows up as a spike of the mean absolute grayscale difference far above its running median.
Usage (gmr env): python detect_cuts.py <video> [--ratio 4.0] [--min_abs 12]
Prints cut frame indices (frame i = first frame of the new shot) and the spike values.
"""
import argparse

import cv2
import numpy as np

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--ratio", type=float, default=4.0, help="spike / local median threshold")
    # 20: fast flash motion in a mostly static shot reached 12-17; the real cuts seen so far were 23-42
    ap.add_argument("--min_abs", type=float, default=20.0, help="minimum absolute mean diff (0-255)")
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    prev, diffs = None, [0.0]
    while True:
        ok, f = cap.read()
        if not ok:
            break
        g = cv2.cvtColor(cv2.resize(f, (160, int(160 * f.shape[0] / f.shape[1]))), cv2.COLOR_BGR2GRAY).astype(np.float32)
        if prev is not None:
            diffs.append(float(np.abs(g - prev).mean()))
        prev = g
    d = np.array(diffs)
    cuts = []
    for i in range(1, len(d)):
        lo, hi = max(1, i - 15), min(len(d), i + 16)
        med = np.median(np.r_[d[lo:i], d[i + 1:hi]]) + 1e-3
        if d[i] > a.min_abs and d[i] / med > a.ratio:
            cuts.append((i, round(d[i], 1), round(d[i] / med, 1)))
    print(f"{a.video.split('/')[-1]}: {len(d)} frames, median diff {np.median(d):.1f}; cuts: {cuts}")
