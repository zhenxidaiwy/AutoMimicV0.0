"""Generic check: would the flip-family terminations fire on the REFERENCE itself, and how much do the flip-family
ABSOLUTE rewards (not relative to the reference) pay the reference?  A termination the reference triggers, or a
reward the reference itself scores low on, teaches the policy that the skill is forbidden.  Mirrors rl/flip_rewards.py
(term_flight_spread, term_leg_twist, term_stand_fail, term_hip_extended; flip_land, flip_leg_sym, flip_land_balance)
in numpy.  A term whose params are null is off.  Last line: AUDIT {json} (machine-readable, read by harness.py).
Usage (unitree_rl_mjlab env): python ref_term_audit.py <ref npz> <labels npz> [terms json]"""
import json
import sys

import numpy as np

z = np.load(sys.argv[1])
L = np.load(sys.argv[2])
terms = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
names = [str(x) for x in L["phase_names"]]
n = len(z["joint_pos"])
ph = L["phase"][:n]
bq, bp, q = z["body_quat_w"], z["body_pos_w"], z["joint_pos"]
ANK, KNEE, TORSO = (6, 12), (4, 10), 15            # mjlab G1 body order
HIP_ROLL, HIP_YAW, HIP_PITCH, WAIST_YAW = (1, 7), (2, 8), (0, 6), 12   # joint order (left, right)


def P(k):
  return names.index(k) if k in names else -1


since = np.zeros(n, int)
for t in range(1, n):
  since[t] = since[t - 1] + 1 if ph[t] == ph[t - 1] else 0
air = (ph == P("flight")) | ((ph == P("land")) & (since < 10))
feet = np.linalg.norm(bp[:, ANK[0], :2] - bp[:, ANK[1], :2], axis=-1)
w, x, y, zz = bq[:, 0, 0], bq[:, 0, 1], bq[:, 0, 2], bq[:, 0, 3]
yax = np.stack([2 * (x * y - w * zz), 1 - 2 * (x * x + zz * zz), 2 * (y * zz + w * x)], -1)
ksep = np.abs(((bp[:, KNEE[0]] - bp[:, KNEE[1]]) * yax).sum(-1))
qt = bq[:, TORSO]
tilt = np.degrees(np.arccos(np.clip(1 - 2 * (qt[:, 1] ** 2 + qt[:, 2] ** 2), -1, 1)))
ld = np.where(ph == P("land"))[0]
landed = np.arange(n) >= (ld[0] if len(ld) else 10 ** 9)
after = ((ph == P("settle")) | (ph == P("stand"))) & landed

# terms json = the FULL set of flip terminations the training gets (as train_dance --flip-terms); null = off
DEF = {"term_flight_spread": {"max_d": 0.6}, "term_leg_twist": {"max_roll": 0.6, "max_yaw": 0.8, "max_knee_sep": 0.45},
       "term_stand_fail": {"max_d": 0.5, "max_tilt": 35.0, "max_waist": 0.6}, "term_hip_extended": {"max_hip": 1.2}}
c = {k: {**DEF[k], **(terms.get(k) or {})} for k in DEF}
active = {k for k, v in terms.items() if v is not None}
fire = {
  "term_flight_spread": air & (feet > c["term_flight_spread"]["max_d"]),
  "term_leg_twist": air & ((np.abs(q[:, HIP_ROLL]) > c["term_leg_twist"]["max_roll"]).any(-1)
                           | (np.abs(q[:, HIP_YAW]) > c["term_leg_twist"]["max_yaw"]).any(-1)
                           | (ksep > c["term_leg_twist"]["max_knee_sep"])),
  "term_stand_fail": after & ((feet > c["term_stand_fail"]["max_d"]) | (tilt > c["term_stand_fail"]["max_tilt"])
                              | (np.abs(q[:, WAIST_YAW]) > c["term_stand_fail"]["max_waist"])),
  "term_hip_extended": (ph == P("flight")) & (q[:, HIP_PITCH].mean(-1) > c["term_hip_extended"]["max_hip"]),
}
fire = {k: v for k, v in fire.items() if k in c and k in active}
print(f"reference {n} frames; air window (flight + first 0.2 s of land): {int(air.sum())} frames; after landing: "
      f"{int(after.sum())} frames")
for k, f in fire.items():
  idx = np.where(f)[0]
  print(f"{k:20s} {c[k]}  fires on the reference in {len(idx)} frames" + (f" ({idx[0]}-{idx[-1]})" if len(idx) else ""))
w_ = np.where(air)[0]
if len(w_):
  print(f"  air window: feet {feet[w_].min():.2f}-{feet[w_].max():.2f} m, knee sep {ksep[w_].min():.2f}-"
        f"{ksep[w_].max():.2f} m, |hip roll| max {np.abs(q[w_][:, HIP_ROLL]).max():.2f}, |hip yaw| max "
        f"{np.abs(q[w_][:, HIP_YAW]).max():.2f}")
a_ = np.where(after)[0]
if len(a_):
  print(f"  after landing: feet max {feet[a_].max():.2f} m, tilt max {tilt[a_].max():.0f} deg, |waist yaw| max "
        f"{np.abs(q[a_, WAIST_YAW]).max():.2f}")

# absolute rewards: what the reference itself earns inside each term's gate (1 = full reward)
LEG_L, LEG_R = list(range(0, 6)), list(range(6, 12))
MIRROR = np.array([1.0, -1.0, -1.0, 1.0, 1.0, -1.0])
ank_z = bp[:, ANK, 2]
land_gate = (ph == P("land")) | (ph == P("settle")) | after
rew = {
  "flip_land": (land_gate, np.cos(np.radians(tilt)).clip(min=0) * (ank_z < 0.1).all(-1)),
  "flip_leg_sym": (air, np.exp(-np.abs(q[:, LEG_R] - MIRROR * q[:, LEG_L]).mean(-1) / 0.2)),
  "flip_land_balance": (land_gate, 0.7 * np.exp(-np.linalg.norm(bp[:, 0, :2] - bp[:, ANK, :2].mean(1), axis=-1) / 0.08)
                        + 0.3 * (((ph == P("land")) & (since < 15)) * (q[:, [3, 9]].mean(-1) / 0.6).clip(0, 1)
                                 + ~((ph == P("land")) & (since < 15)))),
}
pays = {}
for k, (gate, r) in rew.items():
  if gate.any():
    pays[k] = round(float(r[gate].mean()), 3)
    worst = np.where(gate)[0][np.argsort(r[gate])[:3]]
    print(f"{k:20s} reference earns {pays[k]:.2f} of 1 in its gate ({int(gate.sum())} frames); worst frames "
          + ", ".join(f"{t}:{r[t]:.2f}" for t in worst))
import json as _j
print("AUDIT " + _j.dumps({"fires": {k: int(f.sum()) for k, f in fire.items()}, "reference_pays": pays}))
