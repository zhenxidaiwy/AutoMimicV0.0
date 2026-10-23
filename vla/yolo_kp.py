"""YOLOv8n-pose keypoints for every clip, exactly as the live client computes them (imgsz 480, conf 0.4, largest
person per frame, no smoothing). Missed frames reuse the previous detection with confidence 0.
Run in the gvhmr env (has ultralytics):  python yolo_kp.py clip1 clip2 ...
Writes ~/projects/dance/vla/kp/<clip>_yolo.npz (same keys as export_kp.py, kp2d_real = YOLO keypoints) and prints
the mean difference to ViTPose (% of image height) per joint group.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

if __name__ == "__main__":
    H = Path.home()
    D, K = H / "projects/dance/data/clips", H / "projects/dance/vla/kp"
    model = YOLO(str(H / "dance_win/live/yolov8n-pose.pt"))
    for cid in sys.argv[1:]:
        cap = cv2.VideoCapture(str(D / f"{cid}.mp4"))
        out, last = [], np.zeros((17, 3), np.float32)
        while True:
            ok, f = cap.read()
            if not ok:
                break
            r = model.predict(f, imgsz=480, conf=0.4, verbose=False)[0]
            if r.keypoints is not None and len(r.keypoints) > 0 and r.boxes is not None and len(r.boxes) > 0:
                b = r.boxes.xyxy.cpu().numpy()
                i = int(np.argmax((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])))
                xy = r.keypoints.xy[i].cpu().numpy()
                cf = r.keypoints.conf[i].cpu().numpy() if r.keypoints.conf is not None else np.ones(17)
                last = np.concatenate([xy, cf[:, None]], 1).astype(np.float32)
                out.append(last)
            else:
                miss = last.copy()
                miss[:, 2] = 0
                out.append(miss)
        kp = np.stack(out)
        vit = np.load(K / f"{cid}.npz")
        T = min(len(kp), len(vit["kp2d_real"]))
        v = vit["kp2d_real"][:T]
        m = (kp[:T, :, 2] > 0.3) & (v[:, :, 2] > 0.3)
        e = np.linalg.norm(kp[:T, :, :2] - v[:, :, :2], axis=-1) / vit["img_wh"][1] * 100
        grp = {"head": range(0, 5), "arms": range(5, 11), "hips": range(11, 13), "legs": range(13, 17)}
        msg = " ".join(f"{g} {e[:, list(j)][m[:, list(j)]].mean():.2f}" for g, j in grp.items())
        d = dict(vit)
        d["kp2d_real"] = kp[:T]
        np.savez(K / f"{cid}_yolo.npz", **d)
        print(f"{cid:<18} T={T} detected {np.mean(kp[:T, :, 2].max(1) > 0):.2f} | YOLO vs ViTPose (% img h): {msg} "
              f"| conf mean yolo {kp[:T, :, 2].mean():.2f} vit {v[:, :, 2].mean():.2f}")
