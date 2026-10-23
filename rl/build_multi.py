"""Concatenate several clip npz files (mjlab tracking format, 50 fps) into one multi-motion npz.

Extra keys (ignored by mjlab's MotionLoader, used by MultiMotionCommand):
  clip_start, clip_end   per-frame index range [start, end) of the clip the frame belongs to
  clip_id                per-frame clip index;  clip_names, clip_dance (per clip)
A companion prior file <out>_prior.npz holds rsi_weight per frame:
  dance-balanced (each dance gets equal total mass), optionally multiplied by the per-frame VLM phase prior.

Usage (any env with numpy): python build_multi.py <out.npz> [--phase] clip1 clip2 ...
"""
import argparse
import json
import os

import numpy as np

KEYS = ("joint_pos", "joint_vel", "body_pos_w", "body_quat_w", "body_lin_vel_w", "body_ang_vel_w")

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("out")
  ap.add_argument("clips", nargs="+")
  ap.add_argument("--variant", default="lock_vlm")
  ap.add_argument("--phase", action="store_true", help="multiply the balance prior by the VLM phase prior")
  ap.add_argument("--balance", default="dance", choices=["dance", "clip"],
                  help="dance: each dance equal mass, clips by length; clip: every clip equal mass")
  a = ap.parse_args()
  DS = os.path.expanduser("~/projects/dance/dataset")
  parts = {k: [] for k in KEYS}
  start, end, cid, w, dance = [], [], [], [], []
  offset = 0
  for i, c in enumerate(a.clips):
    d = np.load(f"{DS}/{c}/g1_{a.variant}_50fps.npz")
    T = len(d["joint_pos"])
    for k in KEYS:
      parts[k].append(d[k])
    start += [offset] * T
    end += [offset + T] * T
    cid += [i] * T
    ann = json.load(open(f"{DS}/{c}/annotation.json", encoding="utf-8"))
    dance.append(ann["move"])
    if a.phase:
      pw = np.load(f"{DS}/{c}/labels_50fps.npz")["rsi_weight"].astype(np.float64)
      pw = pw / pw.sum()
    else:
      pw = np.full(T, 1.0 / T)
    w.append(pw)
    offset += T
  # dance balance: each dance gets equal mass, clips within a dance proportional to their length
  dance_frames = {m: sum(len(x) for x, dm in zip(w, dance) if dm == m) for m in set(dance)}
  if a.balance == "clip":
    prior = np.concatenate([x / len(w) for x in w])  # each x sums to 1 -> every clip gets 1/n_clips
  else:
    prior = np.concatenate([x * len(x) / dance_frames[m] / len(dance_frames) for x, m in zip(w, dance)])
  prior = prior / prior.sum()
  out = {k: np.concatenate(v, 0) for k, v in parts.items()}
  out.update(fps=np.array([50]), clip_start=np.array(start), clip_end=np.array(end), clip_id=np.array(cid),
             clip_names=np.array(a.clips), clip_dance=np.array(dance))
  np.savez(a.out, **out)
  np.savez(a.out.replace(".npz", "_prior.npz"), rsi_weight=prior)
  for i, c in enumerate(a.clips):
    m = np.array(cid) == i
    print(f"{c:<20} {dance[i]:<6} {m.sum():4d} frames  prior mass {prior[m].sum():.3f}")
  print(f"total {offset} frames ({offset / 50:.1f} s) -> {a.out}")
