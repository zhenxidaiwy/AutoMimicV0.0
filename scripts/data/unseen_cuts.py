"""Shot-cut times (seconds) of a video, same detector as detect_cuts.py, plus a per-second camera-motion proxy.

Usage: python -I unseen_cuts.py <video> [--ratio 4.0] [--min_abs 20]
Prints cut times; a cut at t means the new shot starts at t.
"""
import argparse

import cv2
import numpy as np

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--ratio", type=float, default=4.0)
    ap.add_argument("--min_abs", type=float, default=20.0)
    a = ap.parse_args()
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
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
            cuts.append(f"{i / fps:.2f}s(f{i},{d[i]:.0f})")
    print(f"{a.video.split('/')[-1]}: {len(d)} frames @ {fps:.2f} fps = {len(d) / fps:.2f}s; cuts: {' '.join(cuts) or 'none'}")
