"""Palm-down hand support: while a hand is planted (labels hand_L / hand_R), re-solve ONLY that hand's 3 wrist joints
(roll, pitch, yaw) so that the palm faces the floor and the fingers lie horizontal; every other joint and the body are
untouched. Blended in / out over --ramp frames around the contact.
Why (cartwheel_2, 2026-10-25): with the arms matched by position only the hands pointed down along the forearm and
the robot stood on its finger tips; the user wants the palm on the floor as in the GVHMR result.
Palm side of the G1 rubber hand (scripts/data/g1_palm_axis.py): finger tips curl to -y (left) / +y (right) in the
wrist_yaw_link frame -> palm normal -y (left), +y (right); fingers along +x.
Usage (gmr env): python wrist_flat.py <clip> [--src g1] [--ramp 6]   writes data/g1/<clip>/g1_palm.csv (+ .json)"""
import argparse
import json
import os

import mujoco
import numpy as np
from scipy.optimize import minimize

H = os.path.expanduser("~")
XML = f"{H}/projects/GMR/assets/unitree_g1/g1_mocap_29dof.xml"
SIDES = {"L": ("left_wrist_yaw_link", (19, 20, 21), -1.0), "R": ("right_wrist_yaw_link", (26, 27, 28), +1.0)}


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("clip_id")
  ap.add_argument("--src", default="g1")
  ap.add_argument("--ramp", type=float, default=6.0)
  a = ap.parse_args()
  g = f"{H}/projects/dance/data/g1/{a.clip_id}"
  c = np.loadtxt(f"{g}/{a.src}.csv", delimiter=",")
  q = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)
  T = len(q)
  m = mujoco.MjModel.from_xml_path(XML)
  d = mujoco.MjData(m)
  ann = json.load(open(f"{H}/dance_win/data/annotations/{a.clip_id}.json", encoding="utf-8"))
  idx = np.arange(T)
  out = q.copy()
  rep = {}
  for s, (body, dofs, ysign) in SIDES.items():
    planted = np.array(ann.get(f"hand_{s}", [0] * T)[:T]) == 1
    if not planted.any():
      continue
    w = np.clip(1.0 - np.min(np.abs(idx[:, None] - idx[planted][None, :]), 1) / a.ramp, 0.0, 1.0)
    bid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, body)
    lo, hi = m.jnt_range[[j + 1 for j in dofs], 0], m.jnt_range[[j + 1 for j in dofs], 1]

    def axes(x, t):
      d.qpos[:] = out[t]
      d.qpos[[7 + j for j in dofs]] = x
      mujoco.mj_kinematics(m, d)
      R = d.xmat[bid].reshape(3, 3)
      return R[:, 0], ysign * R[:, 1]  # fingers, palm normal (world)

    def cost(x, t):
      f, n = axes(x, t)
      return (1.0 + n[2]) + 2.0 * f[2] ** 2 + 0.01 * np.sum((x - q[t, [7 + j for j in dofs]]) ** 2)

    before, after = [], []
    x_prev = None
    grid = [np.array([r_, p_, y_]) for r_ in np.linspace(lo[0], hi[0], 5) for p_ in np.linspace(lo[1], hi[1], 5)
            for y_ in np.linspace(lo[2], hi[2], 3)]
    for t in np.where(w > 0)[0]:
      # multi-start (v1 started only from the original wrist and the left palm stayed 65 deg from palm-down)
      starts = [q[t, [7 + j for j in dofs]]] + ([x_prev] if x_prev is not None else []) + grid
      best = None
      for x0 in starts:
        r = minimize(cost, np.clip(x0, lo + 1e-3, hi - 1e-3), args=(t,), method="L-BFGS-B",
                     bounds=list(zip(lo + 1e-3, hi - 1e-3)))
        if best is None or r.fun < best.fun - 1e-9:
          best = r
      r = best
      x_prev = r.x
      x_new = (1 - w[t]) * q[t, [7 + j for j in dofs]] + w[t] * r.x
      if planted[t]:
        before.append(np.degrees(np.arccos(np.clip(-axes(q[t, [7 + j for j in dofs]], t)[1][2], -1, 1))))
      out[t, [7 + j for j in dofs]] = x_new
      if planted[t]:
        after.append(np.degrees(np.arccos(np.clip(-axes(x_new, t)[1][2], -1, 1))))
    rep[f"hand_{s}"] = {"palm_down_angle_deg_mean before": round(float(np.mean(before)), 1),
                        "after": round(float(np.mean(after)), 1),
                        "wrist_change_rad_max": round(float(np.abs(out[:, [7 + j for j in dofs]] - q[:, [7 + j for j in dofs]]).max()), 2)}
  others = [k for k in range(7, 36) if k - 7 not in SIDES["L"][1] + SIDES["R"][1]]
  rep["non_wrist_change_max"] = float(np.abs(out[:, others] - q[:, others]).max())
  fixed = np.concatenate([out[:, :3], out[:, [4, 5, 6, 3]], out[:, 7:]], 1)
  np.savetxt(f"{g}/g1_palm.csv", fixed.astype(np.float32), delimiter=",")
  json.dump(rep, open(f"{g}/g1_palm.json", "w"), indent=1)
  print(json.dumps(rep))


if __name__ == "__main__":
  main()
