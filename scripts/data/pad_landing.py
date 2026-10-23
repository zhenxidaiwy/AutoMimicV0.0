"""Backflip probe: append a stand-up tail to a reference that ends right at the landing (backflip_3 kept only 6
frames after touchdown, so the policy never learned to stand after landing and the evaluation stopped mid-landing).
Tail (30 fps csv): 0.5 s joint + root interpolation from the last frame to the clip's first (standing) frame's joint
pose and an upright root with the last frame's yaw, then 0.7 s hold. Then the 50 fps npz via to_npz.sh and labels
extended with "settle" / "stand", contacts planted.
Usage (gmr env): python pad_landing.py <clip> <variant>   (writes data/g1/<clip>/g1_<variant>_pad.csv)
then: bash to_npz.sh -v <variant>_pad <clip>; python pad_landing.py <clip> <variant> --labels
"""
import sys
from pathlib import Path

import numpy as np
from scipy.spatial.transform import Rotation as R, Slerp

H = Path.home()
clip, var = sys.argv[1], sys.argv[2]
G = H / "projects/dance/data/g1" / clip
DS = H / "projects/dance/dataset" / clip
if "--labels" not in sys.argv:
  c = np.loadtxt(G / f"g1_{var}.csv", delimiter=",")
  n_in, n_hold = 15, 21
  last, first = c[-1], c[0]
  yaw = R.from_quat(last[3:7]).as_euler("zyx")[0]
  up = R.from_euler("z", yaw)
  sl = Slerp([0, 1], R.concatenate([R.from_quat(last[3:7]), up]))
  tail = []
  for i in range(1, n_in + n_hold + 1):
    s = min(i / n_in, 1.0)
    s = 0.5 - 0.5 * np.cos(np.pi * s)  # smooth
    f = last.copy()
    f[2] = last[2] + (first[2] - last[2]) * s
    f[3:7] = sl([s]).as_quat()[0]
    f[7:] = last[7:] + (first[7:] - last[7:]) * s
    tail.append(f)
  out = np.concatenate([c, np.array(tail)], 0)
  np.savetxt(G / f"g1_{var}_pad.csv", out.astype(np.float32), delimiter=",")
  print(f"{clip}: {len(c)} -> {len(out)} frames (+{n_in} stand-up, +{n_hold} hold), root z {last[2]:.3f} -> {first[2]:.3f}")
else:
  z = np.load(DS / "labels_50fps.npz")
  names = [str(x) for x in z["phase_names"]]
  T50 = len(np.load(G / f"g1_{var}_pad_50fps.npz")["joint_pos"])
  n0 = len(z["phase"])
  extra = T50 - n0
  n_settle = int(round(15 / 30 * 50))
  ph = np.concatenate([z["phase"], [names.index("settle")] * min(n_settle, extra),
                       [names.index("stand")] * max(extra - n_settle, 0)])
  cl = np.concatenate([z["contact_L"], np.ones(extra, int)])
  cr = np.concatenate([z["contact_R"], np.ones(extra, int)])
  w = np.concatenate([z["rsi_weight"], np.full(extra, float(np.median(z["rsi_weight"])))])
  np.savez(DS / "labels_pad_50fps.npz", phase=ph, phase_names=z["phase_names"], contact_L=cl, contact_R=cr,
           rsi_weight=w / w.sum())
  print(f"{clip}: labels {n0} -> {T50} frames (+{min(n_settle, extra)} settle, +{max(extra - n_settle, 0)} stand)")
