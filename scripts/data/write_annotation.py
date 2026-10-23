"""Expand compact VLM event annotations into per-frame labels.

Input : data/annotations/<clip_id>.events.json  (written by the annotator: segments + events, see SCHEMA below)
Output: data/annotations/<clip_id>.json          per-frame phase, contact_L/R (1 planted, 0 air, -1 unsure),
                                                  rsi_weight, plus the original events
Usage (any env with numpy): python write_annotation.py <clip_id>

SCHEMA of events.json
{
  "clip_id", "source": {"platform","id","start_s","end_s"}, "fps": 30, "n_frames",
  "camera": "static|moving", "people": 1, "full_body": true, "performer": str, "move": "闪身步|狗熊哆嗦毛|...",
  "quality": 1-5, "notes": str,
  "phases": [[start, end_inclusive, label], ...]           # labels from PHASE_WEIGHT keys
  "swing": [[start, end_inclusive, "L"|"R"], ...]          # one foot in the air, other planted
  "unsure": [[start, end_inclusive], ...]                  # both feet moving / blurred: contact unknown
  "airborne": [[start, end_inclusive], ...]                # both feet clearly off the floor
}
Frames not covered by swing/unsure/airborne are labelled double support.
"""
import json
import os
import sys

import numpy as np

# RSI prior: how hard / informative each phase is to start an episode from (relative, normalised later)
PHASE_WEIGHT = {"ready": 0.3, "stand": 0.3, "prep": 1.0, "flash": 3.0, "hold": 2.0, "recover": 3.0,
                "settle": 1.5, "shake": 2.5, "other": 1.0,
                # backflip (capability probe): counter-movement squat, push-off, flight (both feet off), landing
                "crouch": 1.5, "takeoff": 4.0, "flight": 4.0, "land": 3.0}

if __name__ == "__main__":
    cid = sys.argv[1]
    A = os.path.expanduser("~/dance_win/data/annotations")
    ev = json.load(open(f"{A}/{cid}.events.json", encoding="utf-8"))
    T = ev["n_frames"]
    phase = ["other"] * T
    for s, e, lab in ev["phases"]:
        assert lab in PHASE_WEIGHT, lab
        for t in range(s, min(e, T - 1) + 1):
            phase[t] = lab
    cl, cr = np.ones(T, int), np.ones(T, int)
    for s, e, foot in ev.get("swing", []):
        (cl if foot == "L" else cr)[s:e + 1] = 0
    for s, e in ev.get("unsure", []):
        cl[s:e + 1] = -1
        cr[s:e + 1] = -1
    for s, e in ev.get("airborne", []):
        cl[s:e + 1] = 0
        cr[s:e + 1] = 0
    w = np.array([PHASE_WEIGHT[p] for p in phase], float)
    w /= w.sum()
    out = dict(ev)
    out.update({"phase": phase, "contact_L": cl.tolist(), "contact_R": cr.tolist(),
                "rsi_weight": np.round(w, 6).tolist(),
                "label_convention": "L/R = performer's own left/right; contact 1 planted, 0 air, -1 unsure"})
    json.dump(out, open(f"{A}/{cid}.json", "w", encoding="utf-8"), ensure_ascii=False)
    n = {k: phase.count(k) for k in PHASE_WEIGHT if phase.count(k)}
    print(cid, "frames", T, "| phases", n, "| L air", int((cl == 0).sum()), "R air", int((cr == 0).sum()),
          "unsure", int((cl == -1).sum()))
