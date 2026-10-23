"""Diagnostic library of the harness (paper: Fig. 1c). A check = what to compare with the reference, in which phases,
with what tolerance, and which fix template to switch on when it fails. The harness
  1 builds the initial checklist from the reference when it gets a task (init_from_reference),
  2 evaluates every check after each round (critic.py),
  3 adds a NEW check whenever the critic's full sweep finds a deviation no check covers (grow), and
  4 turns failing checks into reward terms (active_fixes), so the list keeps growing during the recursion and is
    carried over to the next skill.
File: rl/flip_auto/library.json   (human-added checks carry origin "user")
"""
import json
from pathlib import Path

import numpy as np

LIB = Path(__file__).resolve().parent / "library.json"
PAIRS = {"hip_pitch": 1, "hip_roll": -1, "hip_yaw": -1, "knee": 1, "ankle_pitch": 1, "ankle_roll": -1,
         "shoulder_pitch": 1, "shoulder_roll": -1, "shoulder_yaw": -1, "elbow": 1, "wrist_roll": -1}
TOL = {"joint": float(np.radians(15)), "body": 0.08, "jitter": 3.0, "asymmetry": float(np.radians(10)),
       "timing": 3.0, "contact": 3.0}


def base_of(name):
  return name.replace("_joint", "").replace("_link", "").replace("left_", "").replace("right_", "")


def check_id(kind, target, phase):
  return f"{kind}:{target}:{phase}"


def fix_for(kind, target, phase, joint_names, body_names):
  """generic fix template for a check (None = handled by the fixed technique rewards / harness rules)."""
  ph = [phase]
  if kind == "joint":
    js = [j for j in joint_names if base_of(j) == target] or [target]
    return {"func": "dyn_joint", "params": {"joints": js, "phases": ph, "std": 0.3}}
  if kind == "body":
    bs = [b for b in body_names if base_of(b) == target] or [target]
    return {"func": "dyn_body", "params": {"bodies": bs, "phases": ph, "std": 0.1}}
  if kind == "jitter":
    js = [j for j in joint_names if base_of(j) == target] or list(joint_names)
    return {"func": "dyn_quiet", "params": {"joints": js, "phases": ph, "std": 1.0}}
  if kind == "asymmetry" and target in PAIRS:
    return {"func": "dyn_sym", "params": {"base": target, "sign": float(PAIRS[target]), "phases": ph, "std": 0.2}}
  if kind == "contact":
    return {"func": "dyn_contact", "params": {"foot": 0 if target.startswith("left") else 1, "phases": ph}}
  return None


def load():
  if LIB.exists():
    return json.loads(LIB.read_text())
  return {"version": 1, "checks": []}


def save(lib):
  LIB.write_text(json.dumps(lib, indent=1))


def add(lib, kind, target, phase, origin, joint_names, body_names, note=""):
  cid = check_id(kind, target, phase)
  if any(c["id"] == cid for c in lib["checks"]):
    return None
  c = {"id": cid, "kind": kind, "target": target, "phase": phase, "tol": TOL.get(kind, 1.0), "origin": origin,
       "note": note, "fix": fix_for(kind, target, phase, joint_names, body_names), "weight": 0.0, "history": []}
  lib["checks"].append(c)
  return c


def phase_names(labels):
  """per-frame phase names with 'stand_after' for the frames after the reference landing."""
  pn = [str(x) for x in labels["phase_names"]]
  ph = labels["phase"]
  land = np.where(ph == pn.index("land"))[0] if "land" in pn else []
  t_land = int(land[0]) if len(land) else len(ph)
  return [("stand_after" if (pn[p] == "stand" and i >= t_land) else pn[p]) for i, p in enumerate(ph)]


def init_from_reference(lib, ref, labels, joint_names, body_names, origin="init"):
  """Initial checklist for a new task, derived from the reference itself:
  - joint checks for the joints that move a lot (> 0.5 rad range) in each phase of the reference
  - body-shape checks for hands, feet, knees in every dynamic phase
  - symmetry checks for every left/right pair that the reference keeps symmetric (< 10 deg) in a phase
  - contact checks for every phase where the reference stands on its feet
  - jitter checks for the quiet phases (settle, stand_after) and a timing check"""
  names = phase_names(labels)
  q = ref["joint_pos"][:len(names)]
  added = []
  for p in dict.fromkeys(names):
    ii = np.array([i for i, n in enumerate(names) if n == p])
    if len(ii) < 3:
      continue
    rng = q[ii].max(0) - q[ii].min(0)
    for b in sorted({base_of(joint_names[j]) for j in np.where(rng > 0.5)[0]}):
      added.append(add(lib, "joint", b, p, origin, joint_names, body_names, "reference moves this joint a lot"))
    if p not in ("stand", "stand_after", "settle"):
      for b in ("ankle_roll", "wrist_yaw", "knee"):
        if any(base_of(x) == b for x in body_names):
          added.append(add(lib, "body", b, p, origin, joint_names, body_names, "hands / feet / knees shape"))
    for base, s in PAIRS.items():
      li, ri = f"left_{base}_joint", f"right_{base}_joint"
      if li in joint_names and ri in joint_names:
        a = np.abs(q[ii, joint_names.index(ri)] - s * q[ii, joint_names.index(li)]).mean()
        if a < np.radians(10):
          added.append(add(lib, "asymmetry", base, p, origin, joint_names, body_names, "reference is symmetric"))
    if p in ("stand", "crouch", "land", "settle", "stand_after"):
      for side in ("left_foot", "right_foot"):
        added.append(add(lib, "contact", side, p, origin, joint_names, body_names, "reference stands on it"))
    if p in ("settle", "stand_after"):
      added.append(add(lib, "jitter", "all", p, origin, joint_names, body_names, "quiet stance"))
  added.append(add(lib, "timing", "whole_body", "crouch..land", origin, joint_names, body_names, "phase timing"))
  return [a for a in added if a]


# Repair ladder (user 2026-10-23: hand-written rewards must stay a first-class capability):
#   1 "template"   generic fix instantiated automatically (dyn_* in flip_rewards.py)
#   2 "custom"     reward / termination CODE written by the agent for a problem no template can express, or when
#                  a template did not reduce the severity for 2 rounds (the harness marks the check "escalate")
#   3 "reference"  repair of the reference data itself (physics priors)
# Hand-written fixes made so far, registered so they are reused by later skills (knob = the harness knob that
# scales them; code = where they live).
CUSTOM_SEED = [
  ("airborne-while-lying", "metric", "flight", "_airborne: whole body > 5 cm and pelvis > 0.45 m (r2: lying + kicking "
   "counted as airborne)", None, "flip_rewards._airborne"),
  ("spin-only-in-air", "spin", "flight", "spin rewarded only when truly airborne (user design)", "weights.flip_spin",
   "flip_rewards.flip_spin"),
  ("two-foot-push-off", "pushoff", "takeoff", "vertical speed only while both feet load", "weights.flip_pushoff",
   "flip_rewards.flip_pushoff"),
  ("legs-spread-air", "termination", "flight", "feet > max_d apart in the air ends the episode (r4 star shape)",
   "terms.term_flight_spread", "flip_rewards.term_flight_spread"),
  ("hips-extended-air", "termination", "flight", "hip pitch > max_hip mid-flight ends the episode (r4/r6 arching)",
   "terms.term_hip_extended", "flip_rewards.term_hip_extended"),
  ("knee-overfold", "tuck", "flight", "hips one-sided, knees two-sided (r6: one-sided knees folded to 2.9 rad)",
   "weights.flip_tuck", "flip_rewards.flip_tuck"),
  ("legs-twisted-lotus", "termination", "flight", "hip roll / yaw / knee separation limits (r7 lotus legs)",
   "terms.term_leg_twist", "flip_rewards.term_leg_twist"),
  ("walk-to-reference", "tracking", "stand_after", "global position: height only after landing (r6 drift)", None,
   "flip_rewards.flip_root_pos"),
  ("waist-twist-heading", "tracking", "stand_after", "global orientation: tilt only after landing (r7 waist 115 deg)",
   None, "flip_rewards.flip_root_ori"),
  ("unstable-stance", "termination", "stand_after", "feet / tilt / waist limits after landing",
   "terms.term_stand_fail", "flip_rewards.term_stand_fail"),
  ("quiet-stance", "quiet", "stand_after", "arm speed / torso spin / action change after landing (r7 trembling)",
   "weights.flip_stand_quiet", "flip_rewards.flip_stand_quiet"),
  ("rotation-spike", "reference", "flight", "angular-momentum-consistent flight rotation (omega ~ 1/I)", None,
   "scripts/data/flight_momentum.py"),
  ("no-stand-up-tail", "reference", "stand_after", "reference padded with a stand-up tail", None,
   "scripts/data/pad_landing.py"),
]


def seed_custom(lib):
  for name, kind, phase, note, knob, code in CUSTOM_SEED:
    cid = f"custom:{name}"
    if not any(c["id"] == cid for c in lib["checks"]):
      lib["checks"].append({"id": cid, "kind": kind, "target": name, "phase": phase, "tol": None,
                            "origin": "agent (hand-written)", "note": note, "level": "reference" if kind == "reference"
                            else "custom", "knob": knob, "code": code, "fix": None, "weight": 0.0, "history": []})


def stagnating(c, rounds=2):
  """a template fix that did not reduce the severity over `rounds` evaluations -> escalate to a hand-written fix."""
  h = [x["severity"] for x in c.get("history", []) if x.get("severity") is not None]
  return c.get("weight", 0) > 0 and len(h) > rounds and min(h[-rounds:]) >= h[-rounds - 1] * 0.9 and h[-1] > 1


def active_fixes(lib):
  """reward terms for the harness: one per check whose fix has been switched on (weight > 0)."""
  out = []
  for c in lib["checks"]:
    if c.get("fix") and c.get("weight", 0) > 0:
      out.append({"name": "lib_" + c["id"].replace(":", "_").replace(".", "_"), "func": c["fix"]["func"],
                  "weight": c["weight"], "params": c["fix"]["params"]})
  return out
