"""Flash amplitude: the human (performer retargeted to G1) vs the canonical clip the robot replays.
Lateral ankle-to-ankle distance in the pelvis heading frame; extra = per-flash peak - median (stance).
Usage (gmr env): python amp_compare.py gym_sss
"""
import json
import os
import sys
from pathlib import Path

import mujoco
import numpy as np

HOME = Path.home()
G1 = HOME / "projects/dance/data/g1"
ANN = HOME / "dance_win/data/annotations"

os.chdir(HOME / "dance_win/live/g1")
m = mujoco.MjModel.from_xml_path("scene_live.xml")
robot_bodies = [m.body(i).name for i in range(1, m.nbody)]
il, ir = robot_bodies.index("left_ankle_roll_link"), robot_bodies.index("right_ankle_roll_link")


def spread(clip):
  z = np.load(G1 / clip / "g1_lock_vlm_50fps.npz")
  bp, bq = z["body_pos_w"], z["body_quat_w"]
  assert bp.shape[1] == len(robot_bodies), (bp.shape, len(robot_bodies))
  d = bp[:, il] - bp[:, ir]
  w, x, y, zz = bq[:, 0, 0], bq[:, 0, 1], bq[:, 0, 2], bq[:, 0, 3]
  yaw = np.arctan2(2 * (w * zz + x * y), 1 - 2 * (y * y + zz * zz))
  return np.abs(-np.sin(yaw) * d[:, 0] + np.cos(yaw) * d[:, 1])


def per_flash(clip):
  ph = json.load(open(ANN / f"{clip}.json", encoding="utf-8"))["phase"]
  sp = spread(clip)
  base = np.median(sp)
  out = []
  for i in range(1, len(ph)):
    if ph[i] == "flash" and ph[i - 1] != "flash":
      j = i
      while j < len(ph) and ph[j] in ("flash", "hold", "recover"):
        j += 1
      a, b = int(i * 50 / 30), int(min(j, len(ph) - 1) * 50 / 30)
      out.append(sp[a:b + 1].max() - base)
  return base, out


for c in [sys.argv[1], "bda_zhao_sss"]:
  base, ex = per_flash(c)
  print(f"{c:<14} stance spread {base:.2f} m; extra spread per flash: " + ", ".join(f"{e:.2f}" for e in ex) +
        f"  (median {np.median(ex):.2f} m)")
