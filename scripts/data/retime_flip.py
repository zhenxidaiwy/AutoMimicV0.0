"""Backflip probe: re-time the reconstructed flip so the rotation is complete at the video's landing frame.

GVHMR's temporal model lags fast rotations (~700 deg/s): at the landing frame L seen in the video the reconstructed
body has only turned 170-300 deg and finishes the flip 4-10 frames later, so the contact labels (feet planted at L)
contradict the pose (feet still up). Fix: find E = first frame after take-off T where the cumulative pitch reaches
(final rotation - 15 deg), then map reconstructed frames [T, E] linearly onto [T, L] (root pos lerp, root quat slerp,
joints lerp); frames before T unchanged, frames after E follow from L on. The clip gets E - L frames shorter.
g1.csv -> g1_raw.csv (kept), retimed result written to g1.csv.   Usage (gmr env): python retime_flip.py 2 3 ...
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R, Slerp

D = Path.home() / "projects/dance/data/g1"
TL = {1: (49, 63), 2: (39, 54), 3: (59, 73), 4: (35, 57), 5: (29, 49), 6: (33, 53), 7: (15, 33), 8: (31, 48),
      9: (29, 45), 10: (37, 53)}
rep = {}
for k in map(int, sys.argv[1:]):
  cid = f"backflip_{k}"
  raw = D / cid / "g1_raw.csv"
  if not raw.exists():
    shutil.copy(D / cid / "g1.csv", raw)
  c = np.loadtxt(raw, delimiter=",")
  T, L = TL[k]
  r = R.from_quat(c[:, 3:7])
  inc = (r[:-1].inv() * r[1:]).as_rotvec()
  ax = inc[T - 5:].sum(0)
  ax /= np.linalg.norm(ax)
  cum = np.concatenate([[0.0], np.cumsum(inc @ ax)])
  cum -= cum[T]
  final = cum[-1]
  E = int(np.argmax(np.abs(cum) >= abs(final) - np.radians(15)))
  if E <= L:
    print(f"{cid}: rotation done at {E} <= landing {L}, no retime")
    rep[cid] = {"E": E, "L": L, "shift": 0}
    continue
  n_new = len(c) - (E - L)
  src = np.concatenate([np.arange(T), T + (np.arange(T, L + 1) - T) * (E - T) / (L - T),
                        E + np.arange(1, n_new - L)])
  i0 = np.floor(src).astype(int).clip(0, len(c) - 1)
  i1 = (i0 + 1).clip(0, len(c) - 1)
  w = (src - i0)[:, None]
  out = c[i0] * (1 - w) + c[i1] * w
  sl = Slerp(np.arange(len(c)), r)
  out[:, 3:7] = sl(np.clip(src, 0, len(c) - 1)).as_quat()
  np.savetxt(D / cid / "g1.csv", out.astype(np.float32), delimiter=",")
  rot_at_L = np.degrees(cum[L])
  print(f"{cid}: rotation at video landing {rot_at_L:.0f} deg, reaches {np.degrees(final) - 15:.0f} deg at frame {E} "
        f"(+{E - L} f) -> flight {T}-{L} now {np.degrees(final):.0f} deg in {(L - T) / 30:.2f} s; frames {len(c)} -> {n_new}")
  rep[cid] = {"rot_at_video_landing_deg": round(float(rot_at_L), 1), "rotation_done_frame": E, "landing_frame": L,
              "lag_frames": E - L, "frames_before": len(c), "frames_after": n_new}
p = D / "retime_flip.json"
old = json.loads(p.read_text()) if p.exists() else {}
p.write_text(json.dumps({**old, **rep}, indent=1))
