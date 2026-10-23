"""Windows-side check: can we read the front camera and run YOLO pose fast enough? (no window is opened)
Usage: <conda>\\envs\\dancecam\\python.exe cam_test.py [model=yolov8n-pose.pt]
"""
import sys
import time

import cv2
from ultralytics import YOLO

if __name__ == "__main__":
    model = YOLO(sys.argv[1] if len(sys.argv) > 1 else "yolov8n-pose.pt")
    cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
    ok, f = cap.read()
    if not ok:
        raise SystemExit("camera not readable")
    print("camera frame", f.shape, "reported fps", cap.get(cv2.CAP_PROP_FPS))
    t_cap, t_pose, n_person = [], [], 0
    for i in range(60):
        t0 = time.time()
        ok, f = cap.read()
        t1 = time.time()
        r = model.predict(f, imgsz=480, conf=0.4, verbose=False)[0]
        t2 = time.time()
        if i >= 5:  # skip warm-up
            t_cap.append(t1 - t0)
            t_pose.append(t2 - t1)
        n_person += int(r.keypoints is not None and len(r.keypoints) > 0)
    cap.release()
    print(f"capture {1000 * sum(t_cap) / len(t_cap):.1f} ms/frame | pose {1000 * sum(t_pose) / len(t_pose):.1f} ms/frame "
          f"-> ~{len(t_pose) / (sum(t_pose) + sum(t_cap)):.1f} fps | frames with a person: {n_person}/60")
