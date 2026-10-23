"""Where does the follow-dance lag / lose amplitude? Uses a bench timeline (server.py --bench <clip> --rec ...),
the clip's VLM phase annotation (human ground truth), and the G1-retargeted motions of the clip and of the
canonical clip (what the human did vs what the robot is asked to replay).
Usage (gmr env):  python analyze_follow.py <timeline.npz> <clip_id>
"""
import json
import sys
from pathlib import Path

import mujoco
import numpy as np

HOME = Path.home()
ANN = HOME / "dance_win/data/annotations"
G1 = HOME / "projects/dance/data/g1"
CANON = {0: "bda_zhao_sss", 1: "bda2_gxdsm_full"}
FLASHY = ("flash", "hold", "recover")  # the "big" part of a 闪身步


def phases(clip):
  return json.load(open(ANN / f"{clip}.json", encoding="utf-8"))["phase"]


def ankle_dy(clip):
  """Lateral ankle-to-ankle distance (m, pelvis heading frame) of the G1-retargeted clip at 50 fps."""
  z = np.load(G1 / clip / "g1_lock_vlm_50fps.npz")
  m = mujoco.MjModel.from_xml_path(str(HOME / "dance_win/live/g1/g1_29dof.xml")) if False else None
  bp, bq = z["body_pos_w"], z["body_quat_w"]
  names = [str(n) for n in z["body_names"]] if "body_names" in z.files else None
  return bp, bq, names


def yaw_rot_inv(q):
  w, x, y, zz = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
  yaw = np.arctan2(2 * (w * zz + x * y), 1 - 2 * (y * y + zz * zz))
  c, s = np.cos(-yaw), np.sin(-yaw)
  return c, s


def lateral_spread(clip, il, ir):
  z = np.load(G1 / clip / "g1_lock_vlm_50fps.npz")
  bp, bq = z["body_pos_w"], z["body_quat_w"]
  d = bp[:, il] - bp[:, ir]
  c, s = yaw_rot_inv(bq[:, 0])
  return np.abs(-s * d[:, 0] + c * d[:, 1])  # y component in the pelvis heading frame


def main():
  tl, clip = sys.argv[1], sys.argv[2]
  z = np.load(tl)
  R, L = z["rec"], float(z["clip_len"])
  starts = z["starts"]
  t, pd, pf, p = R[:, 0], R[:, 1].astype(int), R[:, 2], R[:, 3]
  rob_dy, ref_dy = np.abs(R[:, 4]), np.abs(R[:, 6])
  hp = phases(clip)
  canon_ph = {d: phases(CANON[d]) for d in (0, 1)}
  hum = np.array([hp[min(int((ti % L) * 30), len(hp) - 1)] for ti in t])
  pred = np.array([canon_ph[d][int(f)] if f >= 0 else "-" for d, f in zip(pd, pf)])
  d0 = 0 if "sss" in clip else 1
  ref = np.array([canon_ph[d0][int(np.clip((pi - starts[d0]) * 30 / 50, 0, len(canon_ph[d0]) - 1))] for pi in p])

  # --- phase agreement over time (how often the model / the reference / match the human's current phase)
  big_h = np.isin(hum, FLASHY)
  print(f"ticks {len(t)}, {t[-1]:.1f} s, clip {L:.2f} s ({t[-1] / L:.1f} loops)")
  print(f"human in flash/hold/recover: {big_h.mean():.0%} of the time")
  for name, arr in (("model prediction", pred), ("robot reference", ref)):
    big = np.isin(arr, FLASHY)
    print(f"{name:<17} in flash/hold/recover {big.mean():.0%}; same coarse state as human (big vs small) "
          f"{(big == big_h).mean():.0%}; exact phase match {(arr == hum).mean():.0%}")

  # --- per human flash: when do the model, the reference and the robot react?
  onsets = [i for i in range(1, len(hp)) if hp[i] == "flash" and hp[i - 1] != "flash"]
  peaks_end = {i: next(j for j in range(i, len(hp)) if hp[j] != "flash") for i in onsets}
  rows = []
  for loop in range(int(t[-1] // L) + 1):
    for i in onsets:
      th = loop * L + i / 30.0
      if th < 1.0 or th + 1.5 > t[-1]:
        continue
      w = (t >= th - 0.3) & (t <= th + 1.5)
      tw = t[w]

      def first(mask):
        k = np.where(mask[w])[0]
        return float(tw[k[0]] - th) if len(k) else np.nan
      lat_pred = first(np.isin(pred, ("flash", "hold")))
      lat_ref = first(np.isin(ref, ("flash", "hold")))
      # spread peaks (relative to the median spread = standing stance)
      base_r, base_f = np.median(rob_dy), np.median(ref_dy)
      kr, kf = np.argmax(rob_dy[w]), np.argmax(ref_dy[w])
      th_peak = loop * L + peaks_end[i] / 30.0
      rows.append([th, lat_pred, lat_ref, tw[kf] - th_peak, tw[kr] - th_peak, ref_dy[w][kf] - base_f,
                   rob_dy[w][kr] - base_r])
  rows = np.array(rows)
  print(f"\nper human flash (n={len(rows)}; times relative to the human's flash onset / flash end):")
  print("  human onset  model says flash  reference flash  ref spread peak  robot spread peak  "
        "ref extra spread  robot extra spread")
  for r in rows:
    print(f"  {r[0]:7.2f} s    {r[1]:+6.2f} s         {r[2]:+6.2f} s         {r[3]:+6.2f} s          "
          f"{r[4]:+6.2f} s          {r[5]:.2f} m            {r[6]:.2f} m")
  med = np.nanmedian(rows, 0)
  print(f"  median       {med[1]:+6.2f} s         {med[2]:+6.2f} s         {med[3]:+6.2f} s          "
        f"{med[4]:+6.2f} s          {med[5]:.2f} m            {med[6]:.2f} m")

  # --- amplitude: what the human did (retargeted to G1) vs the canonical clip the robot replays vs the robot
  zz = np.load(G1 / clip / "g1_lock_vlm_50fps.npz")
  print("\nnpz keys:", zz.files)


if __name__ == "__main__":
  main()
