"""Strictly causal 2D keypoints for test clips (what a robot would see frame by frame).

GVHMR's preprocessing smooths the person box with a centred moving average and interpolates missed frames (uses
future frames). Here: per-frame YOLO person detection (no tracking across the future), pick the box closest to the
previous one (first frame: largest), causal EMA on the box (past only; a missed frame reuses the last box), then
ViTPose per frame on that box.
Run in the gvhmr env from ~/projects/GVHMR:  python causal_kp.py clip1 clip2 ...
Writes ~/projects/dance/vla/kp/<clip>_causal.npz (same keys as export_kp.py, kp2d_real replaced) and prints the mean
difference to the offline keypoints.
"""
import sys
from pathlib import Path

import numpy as np
import torch

sys.path.insert(0, str(Path.home() / "projects" / "GVHMR"))
from hmr4d.utils.geo.hmr_cam import get_bbx_xys_from_xyxy  # noqa: E402
from hmr4d.utils.preproc import VitPoseExtractor  # noqa: E402
from hmr4d.utils.video_io_utils import read_video_np  # noqa: E402
from ultralytics import YOLO  # noqa: E402

if __name__ == "__main__":
    H = Path.home()
    D = H / "projects/dance/data"
    K = H / "projects/dance/vla/kp"
    yolo = YOLO(str(H / "projects/GVHMR/inputs/checkpoints/yolo/yolov8x.pt"))
    vit = VitPoseExtractor()
    for cid in sys.argv[1:]:
        video = str(D / "clips" / f"{cid}.mp4")
        frames = read_video_np(video)
        boxes, prev, ema = [], None, None
        for f in frames:
            r = yolo.predict(f[..., ::-1], classes=[0], conf=0.3, verbose=False)[0]
            b = r.boxes.xyxy.cpu().numpy() if r.boxes is not None else np.zeros((0, 4))
            if len(b):
                if prev is None:
                    pick = b[np.argmax((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1]))]
                else:
                    pick = b[np.argmin(np.abs(b - prev).sum(1))]
                prev = pick
            cur = prev if prev is not None else np.array([0, 0, f.shape[1], f.shape[0]], float)
            ema = cur if ema is None else 0.6 * cur + 0.4 * ema  # causal smoothing (past only)
            boxes.append(ema.copy())
        bbx_xys = get_bbx_xys_from_xyxy(torch.tensor(np.array(boxes)).float(), base_enlarge=1.2).float()
        kp = vit.extract(video, bbx_xys).numpy()
        off = np.load(K / f"{cid}.npz")
        T = min(len(kp), len(off["kp2d_real"]))
        m = (kp[:T, :, 2] > 0.5) & (off["kp2d_real"][:T, :, 2] > 0.5)
        diff = np.linalg.norm(kp[:T, :, :2] - off["kp2d_real"][:T, :, :2], axis=-1)[m].mean() / off["img_wh"][1] * 100
        d = dict(off)
        d["kp2d_real"] = kp[:T]
        np.savez(K / f"{cid}_causal.npz", **d)
        print(f"{cid:<18} T={T}  causal vs offline keypoints: {diff:.2f}% of image height")
