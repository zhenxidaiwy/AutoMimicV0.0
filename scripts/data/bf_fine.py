"""Frame-accurate contact sheet of a window, optionally cropped, labelled with time and the 30 fps frame index
relative to --rel (so labels match frame numbers in a clip cut at --rel).

Usage: python -I bf_fine.py <video> <out.png> --start S --end E [--step 2] [--rel S] [--crop x,y,w,h] [--cols 10] [--w 160]
--step is in source frames.
"""
import argparse

import cv2
import numpy as np

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("out")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--step", type=int, default=2)
    ap.add_argument("--rel", type=float, default=None)
    ap.add_argument("--crop", default=None)
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--w", type=int, default=160)
    a = ap.parse_args()
    rel = a.start if a.rel is None else a.rel
    cap = cv2.VideoCapture(a.video)
    fps = cap.get(cv2.CAP_PROP_FPS) or 30
    cap.set(cv2.CAP_PROP_POS_MSEC, a.start * 1000)
    tiles, i = [], 0
    while True:
        t = cap.get(cv2.CAP_PROP_POS_MSEC) / 1000
        ok, f = cap.read()
        if not ok or t > a.end:
            break
        if i % a.step == 0:
            if a.crop:
                x, y, w, h = map(int, a.crop.split(","))
                f = f[y:y + h, x:x + w]
            f = cv2.resize(f, (a.w, int(f.shape[0] * a.w / f.shape[1])))
            cv2.rectangle(f, (0, 0), (92, 18), (0, 0, 0), -1)
            cv2.putText(f, f"{t:.2f} f{round((t - rel) * 30)}", (2, 13), cv2.FONT_HERSHEY_SIMPLEX, 0.38, (255, 255, 255), 1)
            tiles.append(f)
        i += 1
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[k:k + a.cols], 1) for k in range(0, len(tiles), a.cols)]
    cv2.imwrite(a.out, np.concatenate(rows, 0))
    print(a.out, len(tiles), "tiles", f"{fps:.2f}fps")
