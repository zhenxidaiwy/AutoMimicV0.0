"""YOLOv8n-pose keypoints for the live test videos, exactly as cam_client.py computes them (imgsz 480, conf 0.4,
largest person per frame, no smoothing; a missed frame is not sent, i.e. stored with confidence 0 and flagged).
Run on Windows in the live client's env (dancecam):  python kp_live_tests.py [name ...]
(default: every mp4 in ~/projects/dance/live_tests)
Writes ~/projects/dance/vla/kp_live/<name>.npz with kp (T,17,3), sent (T,) bool, fps.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

if __name__ == "__main__":
    H = Path(r"\\wsl.localhost\Ubuntu-22.04\home\user") if sys.platform == "win32" else Path.home()
    D, K = H / "projects/dance/live_tests", H / "projects/dance/vla/kp_live"
    args = sys.argv[1:]
    if args[:1] == ["--pos_train"]:  # extra dancers for the veto recogniser
        D, K, args = H / "projects/dance/data/pos_train", H / "projects/dance/vla/kp_pos", args[1:]
    K.mkdir(parents=True, exist_ok=True)
    model = YOLO(str(Path(__file__).resolve().parent / "yolov8n-pose.pt"))
    names = args or sorted(p.stem for p in D.glob("*.mp4"))
    for n in names:
        if (K / f"{n}.npz").exists():
            print(f"{n}: cached")
            continue
        cap = cv2.VideoCapture(str(D / f"{n}.mp4"))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        kps, sent = [], []
        while True:
            ok, f = cap.read()
            if not ok:
                break
            wh = np.array([f.shape[1], f.shape[0]])
            r = model.predict(f, imgsz=480, conf=0.4, verbose=False)[0]
            if r.keypoints is not None and len(r.keypoints) > 0 and r.boxes is not None and len(r.boxes) > 0:
                b = r.boxes.xyxy.cpu().numpy()
                i = int(np.argmax((b[:, 2] - b[:, 0]) * (b[:, 3] - b[:, 1])))
                xy = r.keypoints.xy[i].cpu().numpy()
                cf = r.keypoints.conf[i].cpu().numpy() if r.keypoints.conf is not None else np.ones(17)
                kps.append(np.concatenate([xy, cf[:, None]], 1).astype(np.float32))
                sent.append(True)
            else:
                kps.append(np.zeros((17, 3), np.float32))
                sent.append(False)
        kp, sent = np.stack(kps), np.array(sent)
        np.savez(K / f"{n}.npz", kp=kp, sent=sent, fps=fps, wh=wh)
        print(f"{n}: T={len(kp)} fps={fps:.1f} detected {sent.mean():.2f}", flush=True)
