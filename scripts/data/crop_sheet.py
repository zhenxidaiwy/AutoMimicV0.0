"""Person-cropped, frame-indexed contact sheet of a clip, for VLM contact / phase annotation.

Uses GVHMR's tracked person box (preprocess/bbx.pt), so feet are large enough to judge ground contact.
Usage (gmr env): python crop_sheet.py <clip_id> [--step 3] [--cols 10] [--h 200] [--start 0] [--end -1]
Output: ~/dance_win/data/qa/<clip_id>/crops_<start>_<end>.png  (tile label = frame index at 30 fps)
"""
import argparse
import os

import cv2
import numpy as np
import torch

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("clip_id")
    ap.add_argument("--step", type=int, default=3)
    ap.add_argument("--cols", type=int, default=10)
    ap.add_argument("--h", type=int, default=200)
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=-1)
    ap.add_argument("--lower", action="store_true", help="crop only the lower 45%% of the box (feet close-up)")
    a = ap.parse_args()

    D = os.path.expanduser("~/projects/dance/data")
    box = torch.load(f"{D}/gvhmr/{a.clip_id}/preprocess/bbx.pt", weights_only=False)["bbx_xyxy"].numpy()
    cap = cv2.VideoCapture(f"{D}/clips/{a.clip_id}.mp4")
    frames = []
    while True:
        ok, f = cap.read()
        if not ok:
            break
        frames.append(f)
    end = len(frames) if a.end < 0 else min(a.end, len(frames))
    # one fixed crop size for the whole sheet (largest box, padded) so body scale is comparable across tiles
    bw = (box[:, 2] - box[:, 0]).max() * 1.15
    bh = (box[:, 3] - box[:, 1]).max() * 1.10
    tiles = []
    for i in range(a.start, end, a.step):
        cx, cy = (box[i, 0] + box[i, 2]) / 2, (box[i, 1] + box[i, 3]) / 2
        x0, y0 = int(cx - bw / 2), int(cy - bh / 2)
        f = cv2.copyMakeBorder(frames[i], 400, 400, 400, 400, cv2.BORDER_CONSTANT)
        c = f[y0 + 400:y0 + 400 + int(bh), x0 + 400:x0 + 400 + int(bw)]
        if a.lower:
            c = c[int(0.55 * c.shape[0]):]
        c = cv2.resize(c, (int(c.shape[1] * a.h / c.shape[0]), a.h))
        cv2.rectangle(c, (0, 0), (42, 18), (0, 0, 0), -1)
        cv2.putText(c, str(i), (2, 14), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        tiles.append(c)
    while len(tiles) % a.cols:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[k:k + a.cols], 1) for k in range(0, len(tiles), a.cols)]
    out_dir = os.path.expanduser(f"~/dance_win/data/qa/{a.clip_id}")
    os.makedirs(out_dir, exist_ok=True)
    out = f"{out_dir}/{'feet' if a.lower else 'crops'}_{a.start}_{end}.png"
    cv2.imwrite(out, np.concatenate(rows, 0))
    print(out, f"{len(frames)} frames, tiles every {a.step}")
