"""events.json for the backflip probe clips.
Take-off T / landing L: VLM reading of frame-indexed contact sheets (every 2 frames, +-2 f; BACKFLIP_README.md).
Crouch start: first frame before T where the retargeted G1 pelvis is 3 cm below its standing height.
Phases: stand -> crouch -> takeoff (last 4 frames before T, feet still planted) -> flight [T, L-1] (both feet
airborne) -> land [L, L+9] -> settle -> stand.  Usage (gmr env): python make_backflip_events.py 4 5 6 8
"""
import json
import sys
from pathlib import Path

import numpy as np

H = Path.home()
A = H / "dance_win/data/annotations"
TL = {1: (49, 63), 2: (39, 54), 3: (59, 73), 4: (35, 57), 5: (29, 49), 6: (33, 53), 7: (15, 33), 8: (31, 48),
      9: (29, 45), 10: (37, 53)}
SRC = {1: ("av75680591", 23.00, 25.90), 2: ("av75680591", 29.00, 31.75), 3: ("av75680591", 35.20, 38.25),
       4: ("av116460269603942", 3.50, 6.90), 5: ("av116460269603942", 8.50, 11.30),
       6: ("av116460269603942", 12.00, 15.20), 7: ("av117438112863924", 25.60, 27.85),
       8: ("av116641228784719", 15.35, 18.65), 9: ("av115505847472177", 62.90, 65.85),
       10: ("av233376646", 1.90, 4.40)}
for k in map(int, sys.argv[1:]):
  cid = f"backflip_{k}"
  c = np.loadtxt(H / "projects/dance/data/g1" / cid / "g1.csv", delimiter=",")
  n = len(c)
  T, L = TL[k]
  z = c[:, 2]
  z0 = float(np.median(z[:max(T - 20, 5)]))
  c0 = T - 4
  while c0 > 1 and z[c0 - 1] < z0 - 0.03:
    c0 -= 1
  land_end = min(L + 9, n - 1)
  settle_end = min(land_end + 10, n - 1)
  phases = [[0, c0 - 1, "stand"], [c0, T - 5, "crouch"], [T - 4, T - 1, "takeoff"], [T, L - 1, "flight"],
            [L, land_end, "land"]]
  if land_end < n - 1:
    phases.append([land_end + 1, settle_end, "settle"])
  if settle_end < n - 1:
    phases.append([settle_end + 1, n - 1, "stand"])
  phases = [p for p in phases if p[1] >= p[0]]
  av, s0, s1 = SRC[k]
  ev = {"clip_id": cid, "source": {"platform": "bilibili", "id": av, "start_s": s0, "end_s": s1},
        "fps": 30, "n_frames": n, "camera": "static", "people": 1, "full_body": True, "performer": "see BACKFLIP_README",
        "move": "后空翻", "quality": 3,
        "notes": "Standing backflip (capability probe). T/L from frame sheets (+-2 f); crouch start from the G1 pelvis.",
        "annotator": "Claude (VLM, frame sheets) + retargeted pelvis height",
        "phases": phases, "swing": [], "unsure": [[T - 2, T - 1], [L, L + 1]], "airborne": [[T, L - 1]]}
  json.dump(ev, open(A / f"{cid}.events.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)
  print(cid, "frames", n, "stand z", round(z0, 3), "phases", phases)
