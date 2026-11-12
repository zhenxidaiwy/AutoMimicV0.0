"""Diagnostic library of the harness (paper Fig. 1c), version 2: three scopes + promotion.

  generic          L0: motion-agnostic checks, lessons and their fixes (any imitation task)
  family:<f>       L1: shared by a motion family (e.g. 'aerial': flips, cartwheels, aerials)
  task:<clip>      L2: instantiated for one clip from its reference, plus what the decider adds while iterating

A task sees view(lib, task) = generic + its family + itself. Entries are either
  measured checks  (kind joint/body/jitter/asymmetry/contact/timing; tolerance; optional template fix dyn_*)
  lessons          (kind 'lesson' / 'termination' / 'reference' / 'metric' / ...: a failure mode found while
                    iterating and the hand-written fix: knob, code location, how to detect it)
Recursive self-improvement on the library:
  - mark_verified: a task check whose template fix was switched on and brought the severity down is 'verified'
  - promote: a signature verified on >= 2 tasks of one family becomes a family entry (with the fix as a prior);
             verified in >= 2 families -> generic. Lessons the decider reports as reused in another task promote the
             same way (decision field 'lessons_used').
  - init_task: a new task instantiates its checks from the reference AND inherits family/generic priors.
  - freeze: before an evaluation skill, generic + family are frozen to library_frozen_<tag>.json (sha256 logged).
File: rl/flip_auto/library.json
"""
import fnmatch
import hashlib
import json
from pathlib import Path

import numpy as np

LIB = Path(__file__).resolve().parent / "library.json"
PAIRS = {"hip_pitch": 1, "hip_roll": -1, "hip_yaw": -1, "knee": 1, "ankle_pitch": 1, "ankle_roll": -1,
         "shoulder_pitch": 1, "shoulder_roll": -1, "shoulder_yaw": -1, "elbow": 1, "wrist_roll": -1}
TOL = {"joint": float(np.radians(15)), "body": 0.08, "jitter": 3.0, "asymmetry": float(np.radians(10)),
       "timing": 3.0, "contact": 3.0}
MEASURED = tuple(TOL)


def base_of(name):
  return name.replace("_joint", "").replace("_link", "").replace("left_", "").replace("right_", "")


def sig(kind, target, phase):
  return f"{kind}:{target}:{phase}"


def fix_for(kind, target, phase, joint_names, body_names):
  """generic fix template for a measured check (None = no template; needs a hand-written fix)."""
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


# ---------------------------------------------------------------- storage / scopes

def load():
  if LIB.exists():
    return json.loads(LIB.read_text())
  return {"version": 2, "tasks": {}, "checks": []}


def save(lib):
  LIB.write_text(json.dumps(lib, indent=1))


def family_of(lib, task):
  return lib.get("tasks", {}).get(task, {}).get("family", "none")


def register_task(lib, task, family, **meta):
  lib.setdefault("tasks", {})[task] = {"family": family, **lib.get("tasks", {}).get(task, {}), **meta}


def in_view(c, lib, task):
  s = c.get("scope", "generic")
  return s == "generic" or s == f"family:{family_of(lib, task)}" or s == f"task:{task}"


def view(lib, task):
  return [c for c in lib["checks"] if in_view(c, lib, task)]


def task_checks(lib, task):
  return [c for c in lib["checks"] if c.get("scope") == f"task:{task}"]


def find(lib, task, kind, target, phase):
  for c in task_checks(lib, task):
    if (c["kind"], c["target"], c["phase"]) == (kind, target, phase):
      return c
  return None


def add(lib, task, kind, target, phase, origin, joint_names, body_names, note=""):
  """new measured check in the task scope (None if it exists)."""
  if find(lib, task, kind, target, phase):
    return None
  c = {"id": f"{task}/{sig(kind, target, phase)}", "scope": f"task:{task}", "kind": kind, "target": target,
       "phase": phase, "tol": TOL.get(kind, 1.0), "origin": origin, "note": note,
       "fix": fix_for(kind, target, phase, joint_names, body_names), "weight": 0.0, "history": [], "verified": []}
  lib["checks"].append(c)
  return c


def by_id(lib):
  return {c["id"]: c for c in lib["checks"]}


# ---------------------------------------------------------------- task initialisation

def phase_names(labels):
  """per-frame phase names with '<rest>_after' (e.g. 'stand_after') for the rest-pose frames after the main event
  (same rule as rl/mimic_generic.event_frame)."""
  pn = [str(x) for x in labels["phase_names"]]
  ph = np.asarray(labels["phase"])
  if "land" in pn and (ph == pn.index("land")).any():
    ev = int(np.where(ph == pn.index("land"))[0][0])
  else:
    ev = len(ph) - 1
    while ev > 0 and ph[ev - 1] == ph[-1]:
      ev -= 1
  rest = pn[int(ph[0])]
  return [(f"{rest}_after" if (pn[p] == rest and i >= ev) else pn[p]) for i, p in enumerate(ph)]


def init_task(lib, task, family, ref, labels, joint_names, body_names, origin=None):
  """Initial checklist for a new task: (1) instantiated from the reference, (2) family / generic priors whose phase
  exists in this clip inherit their verified fix and prior weight."""
  origin = origin or f"init:{task}"
  register_task(lib, task, family)
  names = phase_names(labels)
  q = ref["joint_pos"][:len(names)]
  added = []
  present = list(dict.fromkeys(names))
  rest_after = [p for p in present if p.endswith("_after")]
  for p in present:
    ii = np.array([i for i, n in enumerate(names) if n == p])
    if len(ii) < 3:
      continue
    quiet = p.endswith("_after") or p == "settle" or p == present[0]
    rng = q[ii].max(0) - q[ii].min(0)
    for b in sorted({base_of(joint_names[j]) for j in np.where(rng > 0.5)[0]}):
      added.append(add(lib, task, "joint", b, p, origin, joint_names, body_names, "reference moves this joint a lot"))
    if not quiet:
      for b in ("ankle_roll", "wrist_yaw", "knee"):
        if any(base_of(x) == b for x in body_names):
          added.append(add(lib, task, "body", b, p, origin, joint_names, body_names, "hands / feet / knees shape"))
    for base, s in PAIRS.items():
      li, ri = f"left_{base}_joint", f"right_{base}_joint"
      if li in joint_names and ri in joint_names:
        a = np.abs(q[ii, joint_names.index(ri)] - s * q[ii, joint_names.index(li)]).mean()
        if a < np.radians(10):
          added.append(add(lib, task, "asymmetry", base, p, origin, joint_names, body_names, "reference is symmetric"))
    if "contact_L" in labels.files:
      for side, key in (("left_foot", "contact_L"), ("right_foot", "contact_R")):
        if np.asarray(labels[key])[ii].mean() > 0.9:
          added.append(add(lib, task, "contact", side, p, origin, joint_names, body_names, "reference stands on it"))
    if p == "settle" or p in rest_after:
      added.append(add(lib, task, "jitter", "all", p, origin, joint_names, body_names, "quiet stance"))
  dyn = [p for p in present if p not in (present[0], "settle") and not p.endswith("_after")]
  if dyn:
    added.append(add(lib, task, "timing", "whole_body", "..".join([dyn[0], dyn[-1]]), origin, joint_names, body_names,
                     "phase timing"))
  # priors from the higher scopes
  for c in [c for c in lib["checks"] if c.get("scope") in ("generic", f"family:{family}")]:
    if c["kind"] in MEASURED and c["phase"] in present and c.get("fix"):
      t = find(lib, task, c["kind"], c["target"], c["phase"]) or add(
        lib, task, c["kind"], c["target"], c["phase"], f"prior:{c['scope']}", joint_names, body_names, c.get("note", ""))
      t["fix"] = json.loads(json.dumps(c["fix"]))
      t["weight"] = float(c.get("prior_weight", 0.0))
      t["origin"] = f"prior:{c['scope']}"
      added.append(t)
  return [a for a in added if a]


# ---------------------------------------------------------------- lessons (hand-written fixes, failure modes)
# (name, scope, kind, phase, note, knob, code). Classified 2026-10-23 when the library got scopes.
LESSONS = [
  # generic (any imitation task)
  ("reward-gate-boundary", "generic", "lesson", "rest_after",
   "rest-pose rewards (balance, feet, upright) must cover ALL frames after the main event; r09-r11 walk-off / squat "
   "started exactly at the settle->stand label switch where they stopped. Detect: quant E per-segment drift.",
   None, "rl/mimic_generic.py phase '<rest>_after'"),
  ("fix-std-no-gradient", "generic", "lesson", "any",
   "a template fix exp(-err/std) with err >> std gives no gradient (r08: signal 1e-5). Detect: quant C signal < 0.05; "
   "fix: std of the order of the current error.", None, "quant_report section C"),
  ("config-audit", "generic", "lesson", "any",
   "decided reward terms missing from the training run (r08 old process). Detect: quant F.", None, "quant_report F"),
  ("knobs-truth-from-logs", "generic", "lesson", "any",
   "state knobs can be mutated after a round trained; diff the training logs (r09 curriculum).", None,
   "quant_report F2"),
  ("best-score-not-best-policy", "generic", "lesson", "any",
   "the scalar score can rank the better policy lower (r10 end-tilt threshold); the decider sets the start "
   "checkpoint.", None, "decision field init"),
  ("control-latency", "generic", "robustness", "any",
   "never-trained latency: 20 ms -> 70 % success, 40 ms -> 0 % (r14). Fix: randomised actuator delay.",
   "delay_ms", "rl/mimic_generic.add_action_delay"),
  ("quiet-stance", "generic", "quiet", "rest_after", "arm speed / torso spin / action change after the event (r7)",
   "weights.flip_stand_quiet", "flip_rewards.flip_stand_quiet"),
  ("stand-still-velocity-scale", "generic", "quiet", "rest_after",
   "pelvis-velocity term with scale 0.6 m/s (0.2 gave no gradient at 1.2 m/s, r10)", "weights.flip_stand_still",
   "flip_rewards.flip_stand_still"),
  ("unstable-stance", "generic", "termination", "rest_after", "feet / tilt / waist limits after the event",
   "terms.term_stand_fail", "flip_rewards.term_stand_fail"),
  ("walk-to-reference", "generic", "tracking", "rest_after",
   "global anchor position: height only after the event (r6 walked to the reference landing spot)", None,
   "flip_rewards.flip_root_pos"),
  ("waist-twist-heading", "generic", "tracking", "rest_after",
   "global orientation: tilt only after the event (r7 waist 115 deg)", None, "flip_rewards.flip_root_ori"),
  ("no-rest-tail", "generic", "reference", "rest_after", "reference padded with a rest-pose tail", None,
   "scripts/data/pad_landing.py"),
  ("hold-final-pose-2s", "generic", "reference", "rest_after",
   "user 2026-10-23: after the motion stay stable >= 2 s in the reference's final pose (standing or not), no sway, "
   "good posture. The reference must end with >= 2.5 s of its held final frame (hold_tail.py); every evaluation "
   "records 5 s past the reference (eval_flip --post_s 5); gates hold_* / post_* in stop_criteria.json.",
   "reference.variant", "scripts/data/hold_tail.py"),
  ("ref-passes-terminations", "generic", "termination", "any",
   "the reference itself must pass every active termination (cartwheel_2 r01: the aerial landing terminations "
   "term_flight_spread / term_leg_twist fired on all 10 frames of the reference's own wide landing, so every correct "
   "cartwheel was cut off at touch-down). Guard: harness.ref_audit refuses the round.", "terms.*",
   "rl/flip_auto/ref_term_audit.py"),
  ("rewards-pay-the-reference", "generic", "lesson", "any",
   "an absolute (not reference-relative) reward must pay the reference itself >= 0.8 inside its gate, else it pulls "
   "the policy away from the skill (cartwheel_2 r01: flip_leg_sym 0.04, flip_land_balance 0.62). Detect: "
   "ref_term_audit 'reference_pays' (logged per round as ref_audit).", "weights.*", "rl/flip_auto/ref_term_audit.py"),
  ("planted-feet-on-floor", "generic", "reference", "stand",
   "planted feet level and on the floor in still stances: ground_fix moves only the root, so an uneven monocular "
   "stance left one STRAIGHT leg's sole 2.4-3.8 cm up for the whole held final pose (cartwheel_2). Fix: legs + root "
   "height only, knees >= 0.1 rad.", "reference.variant", "scripts/data/feet_plant.py"),
  ("segment-probe", "generic", "metric", "any",
   "a from-frame-0 failure does not say WHICH part is not learned: start the policy at several reference frames "
   "(cartwheel_2 r02: from frame 60 on 75 % complete and stand, the entry onto the hands lost within 5 steps). "
   "Automatic each round (quant A3); put start-state weight on the failing segments.", "prior.*",
   "rl/eval_segments.py"),
  ("no-lower-than-reference", "generic", "termination", "any",
   "tracking rewards tolerate a shortcut posture: cartwheel_2 r03 bent the elbows BEFORE the hands touched and went "
   "over on head + forearms (pelvis / torso / shoulders / elbows ~0.2 m below the reference's own minimum). Terminate "
   "when a tracked body goes lower than the reference ever does minus a margin (thresholds from the reference, "
   "contact bodies excluded). Detect: floor_contacts.py / body_min_z.py on the eval record.",
   "terms.term_below_reference", "rl/mimic_generic.term_below_reference"),
  ("planted-foot-stays-down", "generic", "termination", "stand",
   "a contact reward at weight 1 did not stop a pointless 10-14 cm step in the first stand (cartwheel_2 r04, r05): "
   "terminate when a foot the reference has planted is > 5 cm above the reference's ankle in still-stance phases.",
   "terms.term_foot_lifted", "rl/mimic_generic.term_foot_lifted"),
  ("train-the-judged-window", "generic", "reference", "rest_after",
   "robustness failed by DRIFT (> 0.3 m under pushes / latency) in the 5 s past the reference, which training never "
   "saw (episodes resample at the reference end; only 2.5 s of hold were trained). Reference hold >= the judged "
   "window (7.5 s, still < the 10 s episode).", "reference.variant", "scripts/data/hold_long.sh"),
  ("robust-drift-v2", "generic", "metric", "rest_after",
   "robustness success under pushes (0.5 m/s every 1-3 s): drift < 0.5 m over the 5 s past the reference (v2), v1 "
   "0.3 m kept alongside; decided by the agent 2026-10-26 (user delegated). Nominal post drift gate unchanged.",
   None, "rl/eval_flip_robust.py"),
  ("hold-on-the-spot", "generic", "quiet", "rest_after",
   "after a push the robot stepped away and stayed (only speed was penalised, global position is free after the "
   "event): reward the pelvis staying at its own first hold position, per episode.", "extra_dyn",
   "rl/mimic_generic.dyn_hold_spot"),
  ("probe-heading-after-event", "generic", "metric", "rest_after",
   "after the main event the heading is free (flip_root_ori): a segment probe counting full orientation error marked a "
   "standing robot 'lost' (cartwheel_2 r04-r06 land start 0.2-0.47 -> 1.0 with tilt only). Two rounds of start-state "
   "weight on 'land' were spent on this artifact.", None, "rl/eval_segments.py"),
  ("contact-check-ref-relative", "generic", "metric", "land",
   "contact checks must only count steps where the REFERENCE has the foot down (a cartwheel lands one foot after the "
   "other).", None, "rl/flip_auto/critic.py"),
  ("closeup-review", "generic", "lesson", "any",
   "sheet tiles (~250 px) hide hand / head contacts: r03 'cartwheel completed' was a head-and-forearm support only "
   "visible in full-resolution frames (closeup.sh) and confirmed by floor_contacts.py.", None,
   "rl/flip_auto/closeup.sh"),
  ("smooth-root-grounding", "generic", "reference", "any",
   "grounding the root per frame on whichever contact is planted jumps when the contact switches (cartwheel_2: foot "
   "-> hand, root -7 cm in 2 frames, ~2 g down with a foot on the floor): root offset by bounded least squares (no "
   "penetration) with a vertical-acceleration penalty.", "reference.variant", "scripts/data/ground_fix.py --qp"),
  ("family-score", "generic", "metric", "any",
   "the round score must fit the family: the aerial score pays airborne time / pelvis rise / 300 deg, meaningless "
   "for a cartwheel (rotation then relative to the reference's own).", None, "rl/flip_auto/harness.score"),
  # family 'hand_support' (cartwheels, round-offs, handstands)
  ("arms-by-position", "family:hand_support", "reference", "support",
   "GMR smplx_to_g1 left-arm rotation offsets are wrong (left elbow locked at -1.05): arms matched by position "
   "(--arm_pos 50) + elbow branch escape; left hand error 22 -> 1.3 cm.", None, "scripts/data/retarget_headless.py"),
  ("palms-down", "family:hand_support", "reference", "support",
   "palm (not fingertips) on the floor while a hand is planted: wrist joints only, multi-start.", None,
   "scripts/data/wrist_flat.py"),
  ("hand-grounding", "family:hand_support", "reference", "support",
   "hand contacts count for the root height (G1 arms scaled 0.8 vs legs 0.9 left the palms 4-12 cm up).", None,
   "scripts/data/ground_fix.py --hands"),
  ("arm-reach", "family:hand_support", "reference", "support",
   "the G1 arm is short relative to the body: with a smooth root the palm stayed 6-25 cm up while the human's was "
   "planted, the reference hovered over one foot for ~0.25 s. Arm joints only (7 per arm) put the planted palm on the "
   "floor (straight arms, as in the video).", "reference.variant", "scripts/data/arm_reach.py"),
  ("hand-friction", "family:hand_support", "physics", "support",
   "stock G1 non-foot collision geoms have condim 1 (frictionless): hands need condim 3, friction 0.6.",
   "hand_friction", "rl/mimic_generic.set_hand_friction"),
  ("wide-stance-termination", "family:hand_support", "termination", "rest_after",
   "stance limits relative to the reference's own landing stance (cartwheel_2 ankles 0.68 m apart vs 0.23 m "
   "backflip).", "terms.term_stand_fail", "flip_rewards.term_stand_fail"),
  # family 'aerial' (flips, aerials, cartwheels)
  ("airborne-while-lying", "family:aerial", "metric", "flight",
   "_airborne: whole body > 5 cm and pelvis > 0.45 m (r2: lying + kicking counted as airborne)", None,
   "flip_rewards._airborne"),
  ("spin-only-in-air", "family:aerial", "spin", "flight", "rotation rewarded only when truly airborne",
   "weights.flip_spin", "flip_rewards.flip_spin"),
  ("two-foot-push-off", "family:aerial", "pushoff", "takeoff", "vertical speed only while both feet load",
   "weights.flip_pushoff", "flip_rewards.flip_pushoff"),
  ("legs-spread-air", "family:aerial", "termination", "flight", "feet > max_d apart in the air (r4 star shape)",
   "terms.term_flight_spread", "flip_rewards.term_flight_spread"),
  ("legs-twisted-lotus", "family:aerial", "termination", "flight", "hip roll / yaw / knee separation limits (r7)",
   "terms.term_leg_twist", "flip_rewards.term_leg_twist"),
  ("balance-after-landing", "family:aerial", "lesson", "stand_after",
   "land / land_balance / feet_together also in stand_after (r12 fix of the r09-r11 walk-off)",
   "weights.flip_land_balance", "flip_rewards.flip_land_balance"),
  ("rotation-spike", "family:aerial", "reference", "flight", "angular-momentum-consistent flight rotation omega~1/I",
   None, "scripts/data/flight_momentum.py"),
  ("ballistic-flight", "family:aerial", "reference", "flight", "flight height from ballistics", None,
   "scripts/data/backflip_redo.sh"),
  ("rotation-lag", "family:aerial", "reference", "flight", "GVHMR rotation lag retimed", None,
   "scripts/data/retime_flip.py"),
  ("landing-metric-first-run", "family:aerial", "metric", "land",
   "landing = end of the FIRST airborne run (r9 hop after landing gave landing_offset 67)", None,
   "rl/eval_flip.py"),
  # task backflip_3 (tuck specifics, decider terms)
  ("hips-extended-air", "task:backflip_3", "termination", "flight", "hip pitch > max_hip mid-flight (r4/r6 arching)",
   "terms.term_hip_extended", "flip_rewards.term_hip_extended"),
  ("knee-overfold", "task:backflip_3", "tuck", "flight", "hips one-sided, knees two-sided (r6 knees 2.9 rad)",
   "weights.flip_tuck", "flip_rewards.flip_tuck"),
  ("hip-tuck-late", "task:backflip_3", "lesson", "flight", "hip tuck 9 steps late (r8): agent_r09_hip_tuck",
   "extra_dyn", "decisions/r09.json"),
  ("arms-in-air", "task:backflip_3", "lesson", "takeoff..land",
   "asymmetric arms -> off-plane twist (r8): agent_r09_arms_air", "extra_dyn", "decisions/r09.json"),
  ("arms-after-landing", "task:backflip_3", "lesson", "stand_after", "agent_r10_arms_stand", "extra_dyn",
   "decisions/r10.json"),
  ("squat-after-landing", "task:backflip_3", "lesson", "stand_after", "straight legs: agent_r11_legs_stand",
   "extra_dyn", "decisions/r11.json"),
]


def seed_lessons(lib):
  for name, scope, kind, phase, note, knob, code in LESSONS:
    cid = f"{scope.split(':')[-1]}/lesson:{name}"
    if any(c["id"] == cid for c in lib["checks"]):
      continue
    lib["checks"].append({"id": cid, "scope": scope, "kind": kind, "target": name, "phase": phase, "tol": None,
                          "origin": "agent (hand-written)", "note": note, "knob": knob, "code": code, "fix": None,
                          "weight": 0.0, "history": [], "verified": [], "used_in": []})


# ---------------------------------------------------------------- recursion on the library

def stagnating(c, rounds=2):
  """a template fix that did not reduce the severity over `rounds` evaluations -> escalate to a hand-written fix."""
  h = [x["severity"] for x in c.get("history", []) if x.get("severity") is not None]
  return c.get("weight", 0) > 0 and len(h) > rounds and min(h[-rounds:]) >= h[-rounds - 1] * 0.9 and h[-1] > 1


def mark_verified(lib, task):
  """a task check is verified when a round trained with its fix on (history weight > 0) ended at severity
  <= max(1, half of the last severity measured with the fix off)."""
  out = []
  for c in task_checks(lib, task):
    h = [x for x in c.get("history", []) if x.get("severity") is not None]
    before = None
    for x in h:
      if not x.get("weight"):
        before = x["severity"]
      elif before is not None and before > 1 and x["severity"] <= max(1.0, 0.5 * before):
        if x["round"] not in c.setdefault("verified", []):
          c["verified"].append(x["round"])
          out.append(c["id"])
        break
  return out


def promote(lib, min_tasks=2):
  """signatures verified on >= min_tasks tasks of one family -> family entry; on >= 2 families -> generic.
  Lessons with used_in on >= min_tasks tasks are promoted the same way. Returns the list of promotions."""
  groups = {}
  for c in lib["checks"]:
    if not str(c.get("scope", "")).startswith("task:"):
      continue
    task = c["scope"][5:]
    if c["kind"] in MEASURED and c.get("verified"):
      groups.setdefault(("m", sig(c["kind"], c["target"], c["phase"])), []).append((task, c))
    for t in c.get("used_in", []):
      groups.setdefault(("l", c["target"]), []).append((t, c))
  done = []
  for (typ, s), items in groups.items():
    tasks = sorted({t for t, _ in items})
    fams = sorted({family_of(lib, t) for t in tasks})
    for f in fams:
      tf = [t for t in tasks if family_of(lib, t) == f]
      if len(tf) >= min_tasks:
        done.append(_upsert(lib, f"family:{f}", typ, s, items, tf))
    if len(fams) >= 2:
      done.append(_upsert(lib, "generic", typ, s, items, tasks))
  return [d for d in done if d]


def _upsert(lib, scope, typ, s, items, tasks):
  cid = f"{scope.split(':')[-1]}/{s}" if typ == "m" else f"{scope.split(':')[-1]}/lesson:{s}"
  src = items[-1][1]
  ex = by_id(lib).get(cid)
  if ex is None:
    ex = json.loads(json.dumps(src))
    ex.update({"id": cid, "scope": scope, "history": [], "verified": [], "used_in": [], "origin": "promoted"})
    lib["checks"].append(ex)
  if ex.get("promoted_from") == tasks:
    return None
  ex["promoted_from"] = tasks
  if typ == "m":
    ws = [c.get("weight", 0.0) for _, c in items if c.get("weight")]
    ex["prior_weight"] = float(np.median(ws)) if ws else 1.0
    stds = [c["fix"]["params"]["std"] for _, c in items if c.get("fix") and "std" in c["fix"]["params"]]
    if stds and ex.get("fix"):
      ex["fix"]["params"]["std"] = float(np.median(stds))
  return f"{cid} <- {tasks}"


def active_fixes(lib, task):
  """reward terms for a task's training run: every check in its view whose template fix is on (weight > 0)."""
  out = []
  for c in view(lib, task):
    if c.get("fix") and c.get("weight", 0) > 0 and c["kind"] in MEASURED and c.get("scope") == f"task:{task}":
      out.append({"name": "lib_" + c["id"].replace("/", "_").replace(":", "_").replace(".", "_"),
                  "func": c["fix"]["func"], "weight": c["weight"], "params": c["fix"]["params"]})
  return out


def freeze(lib, tag):
  """snapshot of the generic + family scopes before an evaluation skill (the protocol forbids changing them while
  the skill runs). Returns (path, sha256)."""
  snap = {"version": lib.get("version", 2), "tag": tag,
          "checks": [c for c in lib["checks"] if not str(c.get("scope", "")).startswith("task:")]}
  txt = json.dumps(snap, indent=1, sort_keys=True)
  p = LIB.with_name(f"library_frozen_{tag}.json")
  p.write_text(txt)
  h = hashlib.sha256(txt.encode()).hexdigest()
  lib.setdefault("frozen", []).append({"tag": tag, "sha256": h, "n": len(snap["checks"])})
  return p, h


def waived(check_id, waivers):
  """waivers: list of {'check': id or fnmatch pattern, 'reason': ...} from the decisions (cosmetic deviations)."""
  return any(fnmatch.fnmatch(check_id, w["check"]) for w in waivers)


def summary(lib, task=None):
  rows = lib["checks"] if task is None else view(lib, task)
  cnt = {}
  for c in rows:
    k = (c.get("scope", "generic"), "measured" if c["kind"] in MEASURED else "lesson")
    cnt[k] = cnt.get(k, 0) + 1
  return cnt
