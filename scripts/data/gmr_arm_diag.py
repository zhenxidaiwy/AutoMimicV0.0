"""Diagnose GMR arm retargeting by WHERE the robot's elbows / hands end up vs GMR's own (scaled) human targets, per
frame, for: stock config + elbow branch escape (current retarget_headless), arms by position only (rotation weights
of shoulder / elbow / wrist 0, position weight W in stage 2), and the stock config.
Usage (gmr env): python gmr_arm_diag.py <clip> [every=4] [W=50]   writes data/g1/<clip>/qpos_arm_<variant>.npy"""
import copy
import os
import pathlib
import sys

import mujoco
import numpy as np

sys.stdout = open(os.devnull, "w")  # GMR prints its whole model on construction
GMR_ROOT = pathlib.Path.home() / "projects" / "GMR"
clip = sys.argv[1]
every = int(sys.argv[2]) if len(sys.argv) > 2 else 4
W = float(sys.argv[3]) if len(sys.argv) > 3 else 50.0
pred = pathlib.Path.home() / f"projects/dance/data/gvhmr/{clip}/hmr4d_results.pt"
from general_motion_retargeting import GeneralMotionRetargeting as GMR  # noqa: E402
from general_motion_retargeting.utils.smpl import load_gvhmr_pred_file, get_gvhmr_data_offline_fast  # noqa: E402

smplx_data, body_model, smplx_output, height = load_gvhmr_pred_file(pred, GMR_ROOT / "assets" / "body_models")
frames, fps = get_gvhmr_data_offline_fast(smplx_data, body_model, smplx_output, tgt_fps=30)
ARM = ("shoulder_yaw_link", "elbow_link", "wrist_yaw_link")
PTS = [("left_elbow_link", "left_elbow"), ("left_wrist_yaw_link", "left_wrist"),
       ("right_elbow_link", "right_elbow"), ("right_wrist_yaw_link", "right_wrist")]


def run(variant):
  g = GMR(actual_human_height=height, src_human="smplx", tgt_robot="unitree_g1")
  if variant == "pos_only":
    for tab, pw in ((g.ik_match_table1, 0.0), (g.ik_match_table2, W)):
      for s in ("left", "right"):
        for b in ARM:
          e = tab[f"{s}_{b}"]
          e[1], e[2] = pw, 0.0
    g.setup_retarget_configuration()
  lo = g.model.jnt_range[1:, 0]
  q, err = [], []
  for f in frames:
    x = g.retarget(copy.deepcopy(f)).copy()
    if variant == "escape":
      bad = [j for j in (18, 25) if x[7 + j] < lo[j] + 0.05]
      if bad:
        e0 = g.error1() + g.error2()
        y = x.copy()
        for j in bad:
          y[7 + j] = 1.0
        g.configuration.update(y)
        x2 = g.retarget(copy.deepcopy(f)).copy()
        if g.error1() + g.error2() < e0:
          x = x2
        else:
          g.configuration.update(x)
    d = g.configuration.data
    err.append([np.linalg.norm(d.xpos[g.model.body(rb).id] - g.scaled_human_data[hb][0]) for rb, hb in PTS])
    q.append(x)
  return np.array(q), np.array(err) * 100


res = {v: run(v) for v in ("stock", "escape", "pos_only")}
sys.stdout = sys.__stdout__
print("cm distance robot -> human target, per frame:  elbow L, hand L, elbow R, hand R")
print("frame | " + " | ".join(f"{v:>8s}: eL  hL  eR  hR" for v in res))
for t in range(0, len(frames), every):
  print(f"{t:4d}  | " + " | ".join(" ".join(f"{x:4.0f}" for x in res[v][1][t]) for v in res))
for v, (q, e) in res.items():
  print(f"{v:8s} mean cm: elbow L {e[:, 0].mean():.1f} hand L {e[:, 1].mean():.1f} elbow R {e[:, 2].mean():.1f} "
        f"hand R {e[:, 3].mean():.1f}")
  np.save(pathlib.Path.home() / f"projects/dance/data/g1/{clip}/qpos_arm_{v}.npy", q)
