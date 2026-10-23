"""Backflip probe: did GVHMR / the G1 retarget reproduce the flip?
Per clip: cumulative body pitch (rad, unwrapped, about the axis the body actually rotates around) and pelvis height,
for the GVHMR SMPL global trajectory and for the retargeted G1 (g1.csv), plus ballistic check of the annotated
flight (take-off T, landing L from BACKFLIP_README: apex rise = g * t_flight^2 / 8).
Usage (gmr env): python flip_check.py backflip_1 [...]
"""
import json
import sys
from pathlib import Path

import numpy as np
import torch
from scipy.spatial.transform import Rotation as R

D = Path.home() / "projects/dance/data"
TL = {1: (49, 63), 2: (39, 54), 3: (59, 73), 4: (35, 57), 5: (29, 49), 6: (33, 53), 7: (15, 33), 8: (31, 48),
      9: (29, 45), 10: (37, 53)}


def total_rotation(quats_xyzw):
  """Unwrapped rotation angle of the body relative to frame 0, about the dominant rotation axis."""
  r = R.from_quat(quats_xyzw)
  rel = r[0].inv() * r  # body-frame relative rotations
  rv = rel.as_rotvec()
  ang = np.linalg.norm(rv, axis=-1)
  # unwrap: integrate incremental rotations about the dominant axis
  inc = (r[:-1].inv() * r[1:]).as_rotvec()
  ax = inc.sum(0)
  ax = ax / (np.linalg.norm(ax) + 1e-9)
  cum = np.concatenate([[0.0], np.cumsum(inc @ ax)])
  return cum, ang, ax


out = {}
for cid in sys.argv[1:]:
  k = int(cid.split("_")[-1])
  T, L = TL[k]
  res = {"clip": cid, "takeoff_f": T, "landing_f": L, "flight_s": round((L - T) / 30, 3),
         "ballistic_apex_rise_m": round(9.81 * ((L - T) / 30) ** 2 / 8, 3)}
  h = torch.load(D / "gvhmr" / cid / "hmr4d_results.pt", map_location="cpu", weights_only=False)
  g = h["smpl_params_global"]
  go = g["global_orient"].numpy()
  tr = g["transl"].numpy()
  cum, _, ax = total_rotation(R.from_rotvec(go).as_quat())
  res["gvhmr_total_rot_deg"] = round(float(np.degrees(cum[-1])), 1)
  res["gvhmr_max_rot_deg"] = round(float(np.degrees(np.abs(cum).max())), 1)
  res["gvhmr_rot_axis"] = ax.round(2).tolist()
  up = 1  # GVHMR global frame is y-up
  z = tr[:, up]
  res["gvhmr_pelvis_rise_m"] = round(float(z[T:L + 1].max() - z[:max(T - 15, 1)].mean()), 3)
  res["gvhmr_pelvis_min_drop_m"] = round(float(z[:max(T - 15, 1)].mean() - z[max(T - 15, 0):T + 1].min()), 3)
  c = np.loadtxt(D / "g1" / cid / "g1.csv", delimiter=",")
  cum_g, _, _ = total_rotation(c[:, 3:7])
  res["g1_total_rot_deg"] = round(float(np.degrees(cum_g[-1])), 1)
  res["g1_max_rot_deg"] = round(float(np.degrees(np.abs(cum_g).max())), 1)
  res["g1_root_z_stand"] = round(float(c[:max(T - 15, 1), 2].mean()), 3)
  res["g1_root_z_max_flight"] = round(float(c[T:L + 1, 2].max()), 3)
  res["g1_root_z_min_crouch"] = round(float(c[max(T - 15, 0):T + 1, 2].min()), 3)
  res["rot_deg_per_frame_gvhmr"] = np.round(np.degrees(cum[max(T - 5, 0):L + 6:2]), 0).tolist()
  out[cid] = res
  print(json.dumps(res))
json.dump(out, open(D / "g1" / "flip_check.json", "w"), indent=1)
