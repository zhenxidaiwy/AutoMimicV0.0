"""Recover round 1 after its training process was killed at ~1400/1500 iterations (my mistake: I stopped the
harness task while waiting for it). model_1000 (completed a 339-350 deg flip from standing) becomes round 1's result;
the harness then continues with round 2 warm-started from it. Run in the unitree_rl_mjlab env."""
import json

import harness as h

run = "2026-10-22_17-19-08_flipauto_r01"
r = h.evaluate(run, "model_1000.pt")
r = h.extra_metrics(r)
r["ckpt"], r["score"] = "model_1000.pt", h.score(r)
st = {"rounds": [], "knobs": json.loads(json.dumps(h.DEFAULT)), "best": None}
k0 = json.loads(json.dumps(h.DEFAULT))
for key in ("flip_plane_axis", "flip_plane_rate", "flip_leg_sym", "flip_leg_track", "flip_leg_calm"):
  k0["weights"].pop(key, None)  # round 1 was trained without these terms
why = h.adjust(st["knobs"], r)
st["best"] = {"run": run, "ckpt": "model_1000.pt", "score": r["score"], "round": 1}
st["rounds"].append({"round": 1, "run": run, "minutes": None, "knobs": k0,
                     "ep_len_end": h.ep_len(h.DL / "train_flipauto_r01.log"),
                     "evals": [{x: r[x] for x in ("ckpt", "score", "robot_rotation_deg", "robot_max_rotation_deg",
                                                  "robot_peak_pelvis_m", "pelvis_rise_m", "robot_airborne_s",
                                                  "landed_upright", "end_tilt_deg", "early_fall", "plane_dev_max_deg",
                                                  "plane_dev_mean_deg", "leg_asym_deg", "leg_err_deg") if x in r}],
                     "adjust": ["training killed at ~1400 iters (operator error); model_1000 used"] + why})
h.STATE.write_text(json.dumps(st, indent=1))
h.report(st)
print(json.dumps(st["rounds"][0], ensure_ascii=False))
