"""Find the live video band inside a letterboxed / collage portrait video: rows whose pixels change over time.
Usage (gmr env): python find_band.py <video>  -> prints y0 y1 (rows with temporal std above threshold)"""
import sys

import cv2
import numpy as np

cap = cv2.VideoCapture(sys.argv[1])
fr = []
while True:
  ok, f = cap.read()
  if not ok:
    break
  fr.append(cv2.cvtColor(f, cv2.COLOR_BGR2GRAY).astype(np.float32))
a = np.stack(fr)
row = a.std(0).mean(1)  # temporal std per row
thr = 0.25 * np.percentile(row, 95)
live = np.where(row > thr)[0]
# largest contiguous run of live rows
runs, s = [], live[0]
for i in range(1, len(live)):
  if live[i] != live[i - 1] + 1:
    runs.append((s, live[i - 1]))
    s = live[i]
runs.append((s, live[-1]))
y0, y1 = max(runs, key=lambda r: r[1] - r[0])
print(f"frames {len(a)} size {a.shape[2]}x{a.shape[1]} band {y0} {y1} (h {y1 - y0 + 1}); runs {runs[:6]}")
