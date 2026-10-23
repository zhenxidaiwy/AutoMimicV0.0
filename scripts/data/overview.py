"""Overview mosaics for fast VLM screening: one row per video (8 evenly spaced frames), 8 videos per image.

Usage (gmr env): python overview.py [--per 8] [--frames 8]
Reads ~/projects/dance/data/raw/*.mp4, writes ~/dance_win/data/qa/overview/overview_XX.png and index.txt
(row order). Videos listed in ~/dance_win/data/annotations/screened.txt are skipped.
"""
import argparse
import glob
import os

import cv2
import numpy as np

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=8)
    ap.add_argument("--frames", type=int, default=8)
    ap.add_argument("--w", type=int, default=200)
    a = ap.parse_args()
    raw = sorted(glob.glob(os.path.expanduser("~/projects/dance/data/raw/*.mp4")))
    scr_path = os.path.expanduser("~/dance_win/data/annotations/screened.txt")
    screened = set(open(scr_path).read().split()) if os.path.exists(scr_path) else set()
    raw = [p for p in raw if os.path.basename(p)[:-4] not in screened]
    out = os.path.expanduser("~/dance_win/data/qa/overview")
    os.makedirs(out, exist_ok=True)
    for f in glob.glob(f"{out}/*"):
        os.remove(f)
    th = int(a.w * 9 / 16)
    index = []
    for k in range(0, len(raw), a.per):
        rows = []
        for j, p in enumerate(raw[k:k + a.per]):
            vid = os.path.basename(p)[:-4]
            cap = cv2.VideoCapture(p)
            n = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS) or 30
            tiles = []
            for t in np.linspace(0.05, 0.95, a.frames) * n:
                cap.set(cv2.CAP_PROP_POS_FRAMES, int(t))
                ok, fr = cap.read()
                fr = fr if ok else np.zeros((th, a.w, 3), np.uint8)
                s = min(a.w / fr.shape[1], th / fr.shape[0])  # letterbox (portrait videos stay portrait)
                fr = cv2.resize(fr, (int(fr.shape[1] * s), int(fr.shape[0] * s)))
                canvas = np.zeros((th, a.w, 3), np.uint8)
                y0, x0 = (th - fr.shape[0]) // 2, (a.w - fr.shape[1]) // 2
                canvas[y0:y0 + fr.shape[0], x0:x0 + fr.shape[1]] = fr
                tiles.append(canvas)
            label = np.zeros((th, 150, 3), np.uint8)
            row_id = f"{k // a.per:02d}.{j}"
            cv2.putText(label, row_id, (5, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
            cv2.putText(label, vid[-8:], (5, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
            cv2.putText(label, f"{n / fps:.0f}s", (5, 85), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1)
            rows.append(np.concatenate([label] + tiles, 1))
            index.append(f"{row_id} {vid} {n / fps:.1f}s")
        cv2.imwrite(f"{out}/overview_{k // a.per:02d}.png", np.concatenate(rows, 0))
    open(f"{out}/index.txt", "w").write("\n".join(index) + "\n")
    print(f"{len(raw)} videos -> {(len(raw) + a.per - 1) // a.per} mosaics")
