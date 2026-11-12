"""Generic packaging of a skill clip for the harness (any skill; package_backflip.py is the backflip-specific one).
dataset/<clip>/: g1_<variant>_50fps.npz, annotation.json, labels_50fps.npz with phase ids over a vocabulary that
STARTS with the backflip vocabulary (so the shared reward code, which indexes phases by that list, gates stand /
land / settle correctly) followed by the clip's other labels, foot contacts, hand contacts (hand_L/R) and the
start-state weight, all resampled 30 -> 50 fps.
Usage (gmr env): python package_skill.py <clip> <variant, e.g. lock_vlm>"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np

H = Path.home()
G, DS, ANN = H / "projects/dance/data/g1", H / "projects/dance/dataset", H / "dance_win/data/annotations"
BASE = ["stand", "crouch", "takeoff", "flight", "land", "settle", "other"]  # = rl/flip_rewards.PHASES

cid, var = sys.argv[1], sys.argv[2]
ann = json.load(open(ANN / f"{cid}.json", encoding="utf-8"))
names = BASE + [p for p in dict.fromkeys(ann["phase"]) if p not in BASE]
o = DS / cid
o.mkdir(parents=True, exist_ok=True)
src = G / cid / f"g1_{var}_50fps.npz"
shutil.copy(src, o / src.name)
shutil.copy(ANN / f"{cid}.json", o / "annotation.json")
T30 = len(ann["phase"])
T50 = len(np.load(src)["joint_pos"])
idx = np.minimum(np.round(np.arange(T50) * 30 / 50).astype(int), T30 - 1)
w = np.array(ann["rsi_weight"])[idx]
out = {"phase": np.array([names.index(ann["phase"][i]) for i in idx]), "phase_names": np.array(names),
       "contact_L": np.array(ann["contact_L"])[idx], "contact_R": np.array(ann["contact_R"])[idx],
       "rsi_weight": w / w.sum()}
for s in ("L", "R"):
  if f"hand_{s}" in ann:
    out[f"hand_{s}"] = np.array(ann[f"hand_{s}"])[idx]
np.savez(o / "labels_50fps.npz", **out)
print(f"{cid}: {T30} -> {T50} frames, vocabulary {names}; files {sorted(p.name for p in o.iterdir())}")
