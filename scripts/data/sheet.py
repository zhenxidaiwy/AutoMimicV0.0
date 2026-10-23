"""Timestamped contact sheet of a video, for VLM screening / segmentation.

Usage: python sheet.py <video> <out.png> [--every 1.0] [--start 0] [--end inf] [--cols 8] [--w 220]
Each tile is labelled with its timestamp (seconds) in the top-left corner.
"""
import argparse

import cv2
import numpy as np

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--every", type=float, default=1.0)
    ap.add_argument("--start", type=float, default=0.0)
    ap.add_argument("--end", type=float, default=float("inf"))
    ap.add_argument("--cols", type=int, default=8)
    ap.add_argument("--w", type=int, default=220)
    ap.add_argument("--max_tiles", type=int, default=64)
    a = ap.parse_args()

    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / fps
    end = min(a.end, dur)
    ts = np.arange(a.start, end, a.every)
    if len(ts) > a.max_tiles:  # keep the image readable
        ts = np.linspace(a.start, end - 1e-3, a.max_tiles)
    tiles = []
    for t in ts:
        cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, f = cap.read()
        if not ok:
            continue
        h = int(f.shape[0] * a.w / f.shape[1])
        f = cv2.resize(f, (a.w, h))
        cv2.rectangle(f, (0, 0), (62, 20), (0, 0, 0), -1)
        cv2.putText(f, f"{t:.1f}s", (3, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        tiles.append(f)
    if not tiles:
        raise SystemExit(f"no frames read from {a.video}")
    h = max(t.shape[0] for t in tiles)
    tiles = [cv2.copyMakeBorder(t, 0, h - t.shape[0], 0, 0, cv2.BORDER_CONSTANT) for t in tiles]
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[i:i + a.cols], 1) for i in range(0, len(tiles), a.cols)]
    cv2.imwrite(a.out, np.concatenate(rows, 0))
    print(f"{a.out}: {len(ts)} tiles, video {dur:.1f}s @ {fps:.1f}fps, {int(cap.get(3))}x{int(cap.get(4))}")
