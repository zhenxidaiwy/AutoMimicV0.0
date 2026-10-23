"""Tile frames of a video at given times. Usage: python frames_at.py <video> <out.png> t1 t2 ... [--cols 3]"""
import sys

import cv2
import numpy as np

args = sys.argv[1:]
cols = 3
if "--cols" in args:
  i = args.index("--cols")
  cols = int(args[i + 1])
  del args[i:i + 2]
video, out, times = args[0], args[1], [float(t) for t in args[2:]]
cap = cv2.VideoCapture(video)
fps = cap.get(cv2.CAP_PROP_FPS)
tiles = []
for t in times:
  cap.set(cv2.CAP_PROP_POS_FRAMES, int(t * fps))
  ok, f = cap.read()
  if not ok:
    continue
  f = cv2.resize(f, (f.shape[1] // 2, f.shape[0] // 2))
  cv2.putText(f, f"{t:.2f}s", (8, f.shape[0] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 0), 2)
  tiles.append(f)
while len(tiles) % cols:
  tiles.append(np.zeros_like(tiles[0]))
rows = [np.concatenate(tiles[i:i + cols], 1) for i in range(0, len(tiles), cols)]
cv2.imwrite(out, np.concatenate(rows, 0))
print(out, len(times), "frames")
