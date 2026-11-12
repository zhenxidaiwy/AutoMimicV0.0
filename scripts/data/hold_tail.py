"""Generic (L0) reference repair: make every skill end with a held final pose.

User requirement 2026-10-23: after the motion the robot must stay stable for >= 2 s - standing or whatever the
skill ends in (kneeling, a freeze, ...) - without swaying and with a good posture. The judged window needs frames to
train and evaluate on, so the reference gets a tail that HOLDS ITS OWN FINAL FRAME (no pose is invented): positions
copied, all velocities zero. The labels are extended with the clip's final phase (its rest phase, e.g. 'stand'),
the final contact state and the median start-state weight.

  rest = frames of the final phase run after the main event (rl/mimic_generic.event_frame rule)
  the tail is sized so that rest >= --rest_s (default 2.5 s: 2 s judged window + 0.5 s to settle into it)

Usage (any env with numpy): python hold_tail.py <ref_50fps.npz> <labels_50fps.npz> <out_ref.npz> <out_labels.npz>
                                                 [--rest_s 2.5]"""
import argparse

import numpy as np


def event_frame(ph, names):
  """same rule as rl/mimic_generic.event_frame: first 'land' frame, else the start of the final contiguous run."""
  if "land" in names and (ph == names.index("land")).any():
    return int(np.where(ph == names.index("land"))[0][0])
  i = len(ph) - 1
  while i > 0 and ph[i - 1] == ph[-1]:
    i -= 1
  return i


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("ref")
  ap.add_argument("labels")
  ap.add_argument("out_ref")
  ap.add_argument("out_labels")
  ap.add_argument("--rest_s", type=float, default=2.5)
  a = ap.parse_args()
  z = dict(np.load(a.ref))
  L = dict(np.load(a.labels))
  fps = float(np.asarray(z.get("fps", [50.0])).reshape(-1)[0])
  T = len(z["joint_pos"])
  ph = np.asarray(L["phase"])[:T]
  names = [str(x) for x in L["phase_names"]]
  ev = event_frame(ph, names)
  i = T - 1
  while i > ev and ph[i - 1] == ph[-1]:
    i -= 1
  rest_now = T - i  # final phase run after the event
  need = int(np.ceil(a.rest_s * fps))
  extra = max(need - rest_now, 0)
  for k, v in z.items():
    if k == "fps" or not isinstance(v, np.ndarray) or v.ndim == 0 or len(v) != T:
      continue
    if "vel" in k:
      tail = np.zeros((extra,) + v.shape[1:], v.dtype)
    else:
      tail = np.repeat(v[-1:], extra, axis=0)
    z[k] = np.concatenate([v, tail], 0)
  np.savez(a.out_ref, **z)
  out = {"phase": np.concatenate([ph, np.full(extra, ph[-1], ph.dtype)]), "phase_names": L["phase_names"]}
  for k in ("contact_L", "contact_R", "hand_L", "hand_R"):
    if k in L:
      c = np.asarray(L[k])[:T]
      out[k] = np.concatenate([c, np.full(extra, c[-1], c.dtype)])
  if "rsi_weight" in L:
    w = np.asarray(L["rsi_weight"], float)[:T]
    w = np.concatenate([w, np.full(extra, float(np.median(w)))])
    out["rsi_weight"] = w / w.sum()
  np.savez(a.out_labels, **out)
  print(f"{a.ref}: {T} -> {T + extra} frames; final phase '{names[ph[-1]]}' run {rest_now} -> {rest_now + extra} "
        f"frames ({(rest_now + extra) / fps:.2f} s) held at the final reference frame")


if __name__ == "__main__":
  main()
