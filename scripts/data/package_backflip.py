"""Backflip probe: (1) physics-corrected reference variant, (2) package clips for rl/train_run.sh.

(1) "ballistic": GVHMR under-estimates the flight height (pelvis rise 0.11-0.18 m vs >= 0.39 m implied by the
    flight time), so the reference is not physically consistent (in the air the CoM must follow a parabola). The
    root height over the annotated flight [T, L) is replaced by the chord between take-off and landing plus the free
    fall term 0.5 g (t - tT)(tL - t)  (apex +g tf^2 / 8). Input g1_lock_vlm.csv -> g1_ballistic.csv (then to_npz.sh).
(2) dataset/<clip>/: g1_<variant>_50fps.npz, annotation.json, labels_50fps.npz (phase ids over this script's phase
    list, contacts, rsi_weight resampled to 50 fps).
Usage (gmr env): python package_backflip.py ballistic <clip> ... | python package_backflip.py package <clip> ...
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

H = Path.home()
G, DS, ANN = H / "projects/dance/data/g1", H / "projects/dance/dataset", H / "dance_win/data/annotations"
PHASES = ["stand", "crouch", "takeoff", "flight", "land", "settle", "other"]

mode, clips = sys.argv[1], sys.argv[2:]
for cid in clips:
  ann = json.load(open(ANN / f"{cid}.json", encoding="utf-8"))
  T, L = ann["airborne"][0][0], ann["airborne"][0][1] + 1  # first airborne frame, landing frame
  if mode == "ballistic":
    c = np.loadtxt(G / cid / "g1_lock_vlm.csv", delimiter=",")
    ta, tb = (T - 1) / 30, L / 30
    za, zb = c[T - 1, 2], c[L, 2]
    t = np.arange(T, L) / 30
    before = c[T:L, 2].copy()
    c[T:L, 2] = za + (zb - za) * (t - ta) / (tb - ta) + 0.5 * 9.81 * (t - ta) * (tb - t)
    np.savetxt(G / cid / "g1_ballistic.csv", c.astype(np.float32), delimiter=",")
    print(f"{cid}: flight {L - T} f ({(L - T) / 30:.2f} s), root z max {before.max():.3f} -> {c[T:L, 2].max():.3f} m "
          f"(take-off {za:.3f}, landing {zb:.3f})")
  else:
    o = DS / cid
    o.mkdir(parents=True, exist_ok=True)
    for v in ("lock_vlm", "ballistic"):
      f = G / cid / f"g1_{v}_50fps.npz"
      if f.exists():
        shutil.copy(f, o / f.name)
    shutil.copy(ANN / f"{cid}.json", o / "annotation.json")
    T30 = len(ann["phase"])
    T50 = len(np.load(o / "g1_lock_vlm_50fps.npz")["joint_pos"])
    idx = np.minimum(np.round(np.arange(T50) * 30 / 50).astype(int), T30 - 1)
    w = np.array(ann["rsi_weight"])[idx]
    np.savez(o / "labels_50fps.npz", phase=np.array([PHASES.index(ann["phase"][i]) for i in idx]),
             phase_names=np.array(PHASES), contact_L=np.array(ann["contact_L"])[idx],
             contact_R=np.array(ann["contact_R"])[idx], rsi_weight=w / w.sum())
    print(f"{cid}: packaged {sorted(p.name for p in o.iterdir())}")
