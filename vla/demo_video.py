"""Side-by-side demo: held-out human video (+ skeleton, live dance/phase prediction) | G1 following in simulation.

Usage (gmr env): python demo_video.py <closed_loop_name> [--title "..."]
Reads ~/projects/dance/vla/closed_loop/<name>.{json,mp4} and ~/projects/dance/data/clips/<clip>.mp4
Writes ~/dance_win/videos/vla/<name>_demo.mp4
"""
import argparse
import json
from pathlib import Path

import cv2
import imageio.v2 as imageio
import numpy as np

COCO_EDGES = [(5, 7), (7, 9), (6, 8), (8, 10), (5, 6), (5, 11), (6, 12), (11, 12), (11, 13), (13, 15), (12, 14), (14, 16)]
DANCE = {0: "Shan Shen Bu", 1: "Gou Xiong Duo Suo Mao"}

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("name")
  ap.add_argument("--title", default="")
  ap.add_argument("--h", type=int, default=480)
  ap.add_argument("--dir", default="closed_loop", help="closed_loop or retrieve_loop")
  a = ap.parse_args()
  H = Path.home()
  CL = H / "projects/dance/vla" / a.dir
  rec = json.load(open(CL / f"{a.name}.json"))
  res, log = rec["result"], rec["log"]
  clip = res["clip"]
  kp = np.load(H / "projects/dance/vla/kp" / f"{clip}.npz")["kp2d_real"]
  robot = imageio.mimread(CL / f"{a.name}.mp4", memtest=False)
  cap = cv2.VideoCapture(str(H / "projects/dance/data/clips" / f"{clip}.mp4"))
  human = []
  while True:
    ok, f = cap.read()
    if not ok:
      break
    human.append(f[..., ::-1])
  preds = [l for l in log if "dance" in l]
  out = H / "dance_win/videos/vla"
  out.mkdir(parents=True, exist_ok=True)
  w = imageio.get_writer(out / f"{a.name}_demo.mp4", fps=50, macro_block_size=1, quality=7)
  speed = res.get("speed", 1.0)
  for s, rf in enumerate(robot):
    hi = min(int(s * 0.02 * 30 * speed), len(human) - 1)  # slowed video shows each frame longer
    hf = human[hi].copy()
    for i, j in COCO_EDGES:
      p, q = kp[hi, i], kp[hi, j]
      if p[2] > 0.3 and q[2] > 0.3:
        cv2.line(hf, (int(p[0]), int(p[1])), (int(q[0]), int(q[1])), (0, 255, 120), 2)
    sc = a.h / hf.shape[0]
    hf = cv2.resize(hf, (int(hf.shape[1] * sc) // 2 * 2, a.h))
    rf = cv2.resize(rf, (int(rf.shape[1] * a.h / rf.shape[0]) // 2 * 2, a.h))
    p = [x for x in preds if x["step"] <= s]
    if p:
      cur = p[-1]
      txt = f"{DANCE[cur['dance']]} ({cur['dance_p']:.0%}) | robot plays: {cur['phase']}"
      cv2.rectangle(hf, (0, 0), (hf.shape[1], 28), (0, 0, 0), -1)
      cv2.putText(hf, txt, (6, 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
    cv2.putText(hf, "human (unseen performer)", (6, a.h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    cv2.putText(rf, f"G1 sim  t={s * 0.02:.1f}s", (6, a.h - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 0), 1)
    frame = np.concatenate([hf, rf], 1)
    if a.title:
      bar = np.zeros((30, frame.shape[1], 3), np.uint8)
      cv2.putText(bar, a.title, (8, 21), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
      frame = np.concatenate([bar, frame], 0)
    w.append_data(frame)
  w.close()
  print(out / f"{a.name}_demo.mp4")
