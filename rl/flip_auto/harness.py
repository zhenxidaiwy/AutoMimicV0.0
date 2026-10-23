"""Backflip auto-iteration harness (capability probe), real G1 EDU limits (knee 120 N.m).

Each round: write knobs -> start-state prior -> train (warm start from the best checkpoint so far, lr 3e-4) ->
evaluate every saved 500-step checkpoint of the round from a standing start (eval_flip.py) -> score -> adjust the
knobs with rules that fix the EARLIEST broken link of the skill chain -> REPORT.md + videos/backflip/auto/.
Run (unitree_rl_mjlab env): python harness.py [--rounds 12] [--iters 1500]
State: ~/dance_win/rl/flip_auto/state.json (resumable: rerun continues after the last finished round).

Score (all terms capped): airborne_s/0.35 + 2*rotation/300deg + 2*landed + pelvis_rise/0.15 (max 6).
Rules (earliest failure first):
  1 fell before take-off (tilt > 60 deg before the reference take-off)  -> lean x1.5, crouch/stand prior up
  2 no jump (airborne < 0.1 s or pelvis rise < 5 cm)                    -> pushoff x1.5, takeoff/crouch prior up
  3 jumped, rotation < 250 deg                                         -> spin x1.5
  4 rotation ok, not landed                                            -> land x1.5, land prior up
  5 suspicious: airborne > 0.2 s with pelvis rise < 3 cm (exploit)     -> round rejected, airborne weight / 2
"""
import argparse
import json
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np

H = Path.home()
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
BODIES = ["pelvis", "left_hip_roll_link", "left_knee_link", "left_ankle_roll_link", "right_hip_roll_link",
          "right_knee_link", "right_ankle_roll_link", "torso_link", "left_shoulder_roll_link", "left_elbow_link",
          "left_wrist_yaw_link", "right_shoulder_roll_link", "right_elbow_link", "right_wrist_yaw_link"]


def _joint_names():
  import mujoco
  m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
  return [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]


JOINTS = _joint_names()
RL = HERE.parent
STATE = HERE / "state.json"
CLIP, VAR, FAMILY = "backflip_3", "ballistic", "aerial"  # task = clip; family scope of the diagnostic library
DS = H / "projects/dance/dataset" / CLIP
LOGS = H / "projects/dance/runs/logs/rsl_rl/g1_tracking"
DL = H / "projects/dance_logs"
VID = H / "dance_win/videos/backflip/auto"
DEFAULT = {"flip_rewards": 2.0, "knee_limit": 120.0, "ee_threshold": 0.6, "anchor_pos_threshold": 0.4,
           "weights": {"flip_pushoff": 2.0, "flip_lean": 1.0, "flip_spin": 3.0, "flip_airborne": 1.5,
                       "flip_height": 1.0, "flip_land": 1.0, "flip_plane_axis": 1.5, "flip_plane_rate": 1.0,
                       "flip_leg_sym": 1.0, "flip_leg_track": 1.0, "flip_leg_calm": 0.5, "flip_feet_together": 2.0,
                       "flip_tuck": 2.0, "flip_rot_track": 2.0, "flip_land_balance": 2.0, "flip_stay_down": 1.0,
                       "flip_stand_quiet": 2.0},
           # fidelity curriculum (user 2026-10-23): once the flip flow is complete, fit the green reference harder
           "tracking": {"stage": 0, "scale": 1.0, "std_scale": 1.0},
           "terms": {"term_flight_spread": {"max_d": 0.6}, "term_hip_extended": {"max_hip": 1.2},
                     "term_stand_fail": {"max_d": 0.5, "max_tilt": 35.0},
                     "term_leg_twist": {"max_roll": 0.6, "max_yaw": 0.8, "max_knee_sep": 0.45}},
           "prior": {"stand": 0.4, "crouch": 2.0, "takeoff": 2.0, "flight": 0.3, "land": 1.0, "settle": 0.5,
                     "other": 0.5}}


def sh(cmd, log=None):
  print(f"$ {cmd[:300]}", flush=True)
  with open(log, "w") if log else open("/dev/null", "w") as f:
    return subprocess.run(["bash", "-c", cmd], stdout=f if log else subprocess.PIPE, stderr=subprocess.STDOUT,
                          text=True)


def write_prior(prior, path):
  z = np.load(DS / "labels_50fps.npz")
  names = [str(x) for x in z["phase_names"]]
  w = np.array([prior[names[p]] for p in z["phase"]], np.float64)
  np.savez(path, rsi_weight=w / w.sum())


def evaluate(run, ck):
  cmd = (f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; "
         f"export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA; "
         f"python {RL}/eval_flip.py --ckpt {LOGS}/{run}/{ck} --motion {DS}/g1_{VAR}_50fps.npz --tag auto_{ck[:-3]} "
         f"--knee-limit 120 --labels {DS}/labels_50fps.npz --size 960 720 2>&1 | grep -E '^\\{{'")
  r = sh(cmd)
  try:
    return json.loads(r.stdout.strip().splitlines()[-1])
  except Exception:
    return None


def extra_metrics(res):
  """eval_flip.py reports pelvis_rise_m (peak - own standing height) and early_fall (tilt > 60 deg before the
  reference take-off); default them if an older eval json lacks them."""
  res.setdefault("pelvis_rise_m", round(res["robot_peak_pelvis_m"] - 0.79, 3))
  res.setdefault("early_fall", False)
  return res


def score(r):
  rise = max(r["pelvis_rise_m"], 0.0)
  s = (min(r["robot_airborne_s"] / 0.35, 1) + 2 * min(max(r["robot_rotation_deg"], 0) / 300, 1)
       + float(r["landed_upright"]) + 2 * float(r.get("stand_stable", False)) + min(rise / 0.15, 1))
  if r.get("plane_dev_mean_deg") is not None:  # in-plane flip (user): 1 at 0 deg mean deviation, 0 at >= 45 deg
    s += 1 - min(r["plane_dev_mean_deg"] / 45, 1)
  if r.get("leg_asym_deg") is not None:  # legs symmetric in the air (user): 1 at 0 deg, 0 at >= 30 deg
    s += 1 - min(r["leg_asym_deg"] / 30, 1)
  if r.get("track_body_err_m") is not None:  # fidelity to the green reference: 1 at 0 m, 0 at >= 0.25 m
    s += 1 - min(r["track_body_err_m"] / 0.25, 1)
  return round(s, 3)


def adjust(k, r):
  w, p, why = k["weights"], k["prior"], []
  if r["robot_airborne_s"] > 0.2 and r["pelvis_rise_m"] < 0.03:
    w["flip_airborne"] /= 2
    why.append("suspicious airborne without rise -> airborne weight / 2")
  elif r.get("early_fall"):
    w["flip_lean"] *= 1.5; p["crouch"] *= 1.3; p["stand"] *= 1.3
    why.append("fell before take-off -> lean x1.5, stand/crouch prior x1.3")
  elif r["robot_airborne_s"] < 0.1 or r["pelvis_rise_m"] < 0.05:
    w["flip_pushoff"] *= 1.5; p["takeoff"] *= 1.3; p["crouch"] *= 1.2
    why.append("no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2")
  elif r["robot_rotation_deg"] < 250:
    w["flip_spin"] *= 1.5
    why.append("jumps but rotation < 250 -> spin x1.5")
  elif not r["landed_upright"]:
    w["flip_land"] *= 1.5; p["land"] *= 1.3
    why.append("rotates but does not land -> land x1.5, land prior x1.3")
  else:
    why.append("full flip landed -> keep knobs, train on")
  # independent of the chain: twisting / tilting out of the flip plane (user 2026-10-22)
  if r["robot_airborne_s"] >= 0.1 and (r.get("plane_dev_max_deg") or 0) > 30:
    w["flip_plane_axis"] *= 1.5; w["flip_plane_rate"] *= 1.5
    why.append(f"out of plane (max {r['plane_dev_max_deg']} deg) -> plane weights x1.5")
  if r["robot_airborne_s"] >= 0.1 and ((r.get("leg_asym_deg") or 0) > 15 or (r.get("leg_err_deg") or 0) > 25):
    for t in ("flip_leg_sym", "flip_leg_track", "flip_leg_calm"):
      w[t] *= 1.5
    why.append(f"legs flail (asym {r.get('leg_asym_deg')} deg, err {r.get('leg_err_deg')} deg) -> leg weights x1.5")
  # step-by-step review findings (round 2): early take-off, hips extended instead of tucked, rotation lag, collapse
  if r.get("takeoff_offset_steps") is not None and r["takeoff_offset_steps"] < -3:
    w["flip_stay_down"] *= 1.5
    why.append(f"took off {-r['takeoff_offset_steps']} steps early -> stay-down x1.5")
  if r["robot_airborne_s"] >= 0.1 and (r.get("flight_hip_err_rad") or 0) > 0.6:
    w["flip_tuck"] *= 1.5
    why.append(f"hips not tucked in flight (err {r['flight_hip_err_rad']} rad) -> tuck x1.5")
  if r.get("rot_at_ref_landing_deg") is not None and \
      r["rot_at_ref_landing_deg"] < r.get("ref_rot_at_landing_deg", 0) - 40:
    w["flip_rot_track"] *= 1.5
    why.append(f"rotation late ({r['rot_at_ref_landing_deg']} vs {r['ref_rot_at_landing_deg']} deg at the "
               f"reference landing) -> rot-track x1.5")
  if r["robot_airborne_s"] >= 0.1 and (r.get("pelvis_min_after_landing_m") or 1) < 0.5:
    w["flip_land_balance"] *= 1.5
    why.append(f"collapsed after landing (pelvis {r['pelvis_min_after_landing_m']} m) -> land-balance x1.5")
  # fidelity curriculum: once the whole flow works (full rotation, upright landing, real flight, no early fall),
  # fit the green reference harder every round; back off one step if the flow breaks again
  TR = k.setdefault("tracking", {"stage": 0, "scale": 1.0, "std_scale": 1.0})
  flow_ok = (r["robot_rotation_deg"] >= 320 and r["landed_upright"] and r["robot_airborne_s"] >= 0.3
             and not r.get("early_fall", False))
  if flow_ok:
    TR["stage"] = 1
    TR["scale"] = round(min(TR["scale"] * 1.5, 4.0), 3)
    TR["std_scale"] = round(max(TR["std_scale"] * 0.85, 0.5), 3)
    why.append(f"flow complete -> fidelity stage 1: tracking x{TR['scale']}, std x{TR['std_scale']} "
               f"(body err {r.get('track_body_err_m')} m)")
  elif TR.get("stage", 0) == 1:
    TR["scale"] = round(max(TR["scale"] / 1.5, 1.0), 3)
    TR["std_scale"] = round(min(TR["std_scale"] / 0.85, 1.0), 3)
    why.append(f"flow broken under the fidelity curriculum -> back off: tracking x{TR['scale']}, "
               f"std x{TR['std_scale']}")
  # hard limits: tighten only while the robot still flips (keeps learning alive); floors keep them feasible
  T = k.setdefault("terms", json.loads(json.dumps(DEFAULT["terms"])))
  flips = r["robot_airborne_s"] >= 0.3 and r["robot_rotation_deg"] > 250
  if flips and (r.get("feet_dist_max_m") or 0) > 0.45:
    T["term_flight_spread"]["max_d"] = round(max(T["term_flight_spread"]["max_d"] * 0.9, 0.35), 3)
    why.append(f"feet {r.get('feet_dist_max_m')} m in the air -> spread limit {T['term_flight_spread']['max_d']} m")
  if flips and ((r.get("flight_hip_err_rad") or 0) > 0.6 or (r.get("flight_hip_mean_rad") or -1) > 0):
    T["term_hip_extended"]["max_hip"] = round(max(T["term_hip_extended"]["max_hip"] - 0.3, -0.6), 2)
    why.append(f"hips extended / arched (mean {r.get('flight_hip_mean_rad')} rad) -> hip limit "
               f"{T['term_hip_extended']['max_hip']} rad")
  if flips and ((r.get("knee_sep_max_m") or 0) > 0.45 or (r.get("flight_hip_roll_max_rad") or 0) > 0.6
                or (r.get("flight_hip_yaw_max_rad") or 0) > 0.8):
    TW = T.setdefault("term_leg_twist", {"max_roll": 0.6, "max_yaw": 0.8, "max_knee_sep": 0.45})
    TW["max_roll"] = round(max(TW["max_roll"] - 0.1, 0.3), 2)
    TW["max_yaw"] = round(max(TW["max_yaw"] - 0.1, 0.4), 2)
    TW["max_knee_sep"] = round(max(TW["max_knee_sep"] - 0.05, 0.3), 2)
    why.append(f"legs twisted / knees splayed (sep {r.get('knee_sep_max_m')} m, roll "
               f"{r.get('flight_hip_roll_max_rad')}, yaw {r.get('flight_hip_yaw_max_rad')}) -> twist limits {TW}")
  # quiet stance after landing (user: hands trembling, body swaying while standing)
  if r["landed_upright"] and ((r.get("stand_arm_vel_rms") or 0) > 0.8 or (r.get("stand_torso_angvel") or 0) > 0.3
                              or (r.get("stand_action_change") or 0) > 0.05):
    w["flip_stand_quiet"] = w.get("flip_stand_quiet", 2.0) * 1.5
    why.append(f"not quiet after landing (arm {r.get('stand_arm_vel_rms')} rad/s, torso "
               f"{r.get('stand_torso_angvel')} rad/s, action change {r.get('stand_action_change')}) -> quiet x1.5")
  if flips and (r.get("flight_knee_overfold_rad") or 0) > 0.6:
    w["flip_tuck"] *= 1.5
    why.append(f"knees over-folded by {r['flight_knee_overfold_rad']} rad (legs coiled) -> tuck x1.5")
  if flips and not r.get("stand_stable", False):
    T["term_stand_fail"]["max_d"] = round(max(T["term_stand_fail"]["max_d"] * 0.9, 0.35), 3)
    T["term_stand_fail"]["max_tilt"] = round(max(T["term_stand_fail"]["max_tilt"] - 5, 20), 1)
    why.append(f"not standing stably (feet end {r.get('stand_feet_d_end')} m) -> stand limits "
               f"{T['term_stand_fail']['max_d']} m / {T['term_stand_fail']['max_tilt']} deg")
  if r["robot_airborne_s"] >= 0.1 and (r.get("feet_dist_max_m") or 0) > 0.35:
    w["flip_feet_together"] *= 1.5
    why.append(f"legs spread (feet {r.get('feet_dist_max_m')} m) -> feet-together x1.5")
  for d in (w, p):
    for key in d:  # cap 10: by round 7 the x1.5 rules had pushed leg terms to 17 vs spin 3 (they swamped the flip)
      d[key] = round(min(d[key], 10.0), 4)
  return why


MAX_ACTIVE = 12  # active template fixes at most (by severity), so library rewards cannot pile up


def apply_decision(st, rnd):
  """LLM-in-the-loop (user 2026-10-23: templates/rules only point at problems; solving and prioritising is the
  foundation model's job): decisions/rNN.json written by the agent after analysing round NN-1:
  {"reasoning": "...", "priorities": [...], "knobs": {"dotted.path": value}, "library": {check_id: weight},
   "code_changes": ["..."], "new_checks": [{"kind", "target", "phase", "note"}]}"""
  import copy
  import library as libm
  p = HERE / "decisions" / f"r{rnd:02d}.json"
  if not p.exists():
    return None
  d = json.loads(p.read_text())
  # protocol (user 2026-10-23): quantify -> LLM analysis -> solution -> train. Refuse a decision that skips a step.
  if rnd > 1:
    prev = f"r{rnd - 1:02d}"
    quant, ana = HERE / "analysis" / f"{prev}_quant.md", HERE / "analysis" / f"{prev}_llm.md"
    sheets = sorted((VID / prev).glob("sheet_*.jpg"))
    missing = [str(x) for x in (quant, ana) if not x.exists()]
    unseen = [s.stem.replace("sheet_", "") for s in sheets
              if not any(s.stem.replace("sheet_", "") in r for r in d.get("reviewed_sheets", []))]
    if missing or unseen:
      print(f"=== round {rnd}: decision refused - missing {missing}, sheets not reviewed {unseen}", flush=True)
      return None
    # stop criteria (stop_criteria.py, layered generic / family / task): a finished skill is not trained further
    # unless the decider states why; a skill over budget stops unless the decision overrides the budget
    sp = HERE / "analysis" / f"{prev}_stop.json"
    if sp.exists():
      stop = json.loads(sp.read_text())
      if stop.get("done") and not d.get("continue_reason"):
        print(f"=== round {rnd}: decision refused - skill complete after {prev} (stop criteria); add continue_reason",
              flush=True)
        return None
      if stop.get("over_budget") and not d.get("budget_override"):
        print(f"=== round {rnd}: decision refused - budget exhausted; add budget_override", flush=True)
        return None
  for path, val in d.get("knobs", {}).items():
    node = st["knobs"]
    keys = path.split(".")
    for key in keys[:-1]:
      node = node.setdefault(key, {})
    node[keys[-1]] = copy.deepcopy(val)
  lib = libm.load()
  for c in d.get("new_checks", []):
    libm.add(lib, CLIP, c["kind"], c["target"], c["phase"], f"agent r{rnd}", JOINTS, BODIES, c.get("note", ""))
  # new hand-written lessons go to the task scope (promotion to family / generic happens across tasks)
  for les in d.get("lessons", []):
    cid = f"{CLIP}/lesson:{les['name']}"
    if cid not in libm.by_id(lib):
      lib["checks"].append({"id": cid, "scope": f"task:{CLIP}", "kind": les.get("kind", "lesson"),
                            "target": les["name"], "phase": les.get("phase", "any"), "tol": None,
                            "origin": f"agent r{rnd}", "note": les.get("note", ""), "knob": les.get("knob"),
                            "code": les.get("code"), "fix": None, "weight": 0.0, "history": [], "verified": [],
                            "used_in": [CLIP]})
  for name in d.get("lessons_used", []):  # a lesson of another task / scope reused here -> promotion evidence
    for c in lib["checks"]:
      if c["kind"] not in libm.MEASURED and c["target"] == name and CLIP not in c.setdefault("used_in", []):
        c["used_in"].append(CLIP)
  by_id = libm.by_id(lib)
  resolve = lambda cid: by_id.get(cid) or by_id.get(f"{CLIP}/{cid}")  # decisions may omit the task prefix
  for cid, w in d.get("library", {}).items():
    if resolve(cid):
      resolve(cid)["weight"] = float(w)
  # template parameters chosen by the decider (round 8: std 0.2 vs errors of 1-2 rad -> exp(-10) -> no gradient)
  for cid, params in d.get("library_params", {}).items():
    if resolve(cid) and resolve(cid).get("fix"):
      resolve(cid)["fix"]["params"].update(params)
  libm.save(lib)
  return d


def grow_library(crit, rnd, apply=True):
  """RSI step on the checklist: failing template checks get their fix switched on / strengthened, findings that no
  check covers become NEW checks (with a template fix when one exists), stagnating template fixes are escalated to
  a hand-written fix (the agent writes reward / termination code and registers it as a 'custom' entry)."""
  import library as libm
  lib = libm.load()
  by_id = {c["id"]: c for c in lib["checks"]}
  changes, escalate = [], []
  for s in crit.get("checks", []):
    c = by_id.get(s["id"])
    if c is None or s["pass"] or not c.get("fix"):
      continue
    if s.get("escalate"):
      escalate.append({"check": c["id"], "severity": s["severity"], "detail": s["detail"],
                       "why": "template fix did not reduce the severity for 2 rounds"})
      continue
    if not apply:
      changes.append(f"suggest: fix {c['id']} (severity {s['severity']}, weight now {c.get('weight', 0)})")
      continue
    c["weight"] = round(min(max(c.get("weight", 0) * 1.5, 1.0), 6.0), 3)
    changes.append(f"fix {c['id']} -> weight {c['weight']} (severity {s['severity']})")
  for r in crit.get("new", [])[:6]:
    c = libm.add(lib, CLIP, r["kind"], r["what"], r["phase"], f"critic r{rnd}", JOINTS, BODIES, r["detail"])
    if c is None:
      continue
    if c.get("fix"):
      c["weight"] = 1.0 if apply else 0.0
      changes.append(f"NEW check {c['id']} (severity {r['severity']}) with template fix"
                     + ("" if apply else " (fix not switched on: LLM decides)"))
    else:
      escalate.append({"check": c["id"], "severity": r["severity"], "detail": r["detail"],
                       "why": "no template can express it"})
      changes.append(f"NEW check {c['id']} (severity {r['severity']}) -> needs a hand-written fix")
  # keep at most MAX_ACTIVE template fixes: the ones with the highest last severity
  act = [c for c in libm.task_checks(lib, CLIP) if c.get("fix") and c.get("weight", 0) > 0] if apply else []
  act.sort(key=lambda c: -(c["history"][-1]["severity"] if c.get("history") else 0))
  for c in act[MAX_ACTIVE:]:
    c["weight"] = 0.0
    changes.append(f"fix {c['id']} parked (more than {MAX_ACTIVE} active)")
  libm.save(lib)
  return changes, escalate


def train(rnd, k, init, iters):
  run_name = f"flipauto_r{rnd:02d}"
  prior = DS / f"auto_prior_r{rnd:02d}.npz"
  write_prior(k["prior"], prior)
  import library as libm
  dyn_file = DL / f"dyn_r{rnd:02d}.json"
  # library fixes + terms the decider composed itself (knob extra_dyn: [{"name", "func", "weight", "params"}])
  dyn_file.write_text(json.dumps(libm.active_fixes(libm.load(), CLIP) + k.get("extra_dyn", [])))
  resume = f"--agent.resume True --agent.load-run {init[0]} --agent.load-checkpoint {init[1]}" if init else ""
  cmd = (f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; "
         f"export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off; "
         f"python {RL}/train_dance.py --rsi phase --labels {DS}/labels_50fps.npz --prior {prior} "
         f"--flip-rewards {k['flip_rewards']} --flip-weights '{json.dumps(k['weights'])}' "
         f"--flip-terms '{json.dumps(k.get('terms', {}))}' --dyn-rewards {dyn_file} "
         f"--tracking-scale {k.get('tracking', {}).get('scale', 1.0)} "
         f"--tracking-std-scale {k.get('tracking', {}).get('std_scale', 1.0)} "
         f"--knee-limit {k['knee_limit']} --ee-threshold {k['ee_threshold']} --delay-ms {k.get('delay_ms', 0)} "
         f"--anchor-pos-threshold {k['anchor_pos_threshold']} -- --motion-file {DS}/g1_{VAR}_50fps.npz "
         f"--env.scene.num-envs 4096 --agent.max-iterations {iters} --agent.algorithm.learning-rate 0.0003 "
         f"--agent.run-name {run_name} --agent.logger tensorboard {resume}")
  t0 = time.time()
  sh(cmd, DL / f"train_{run_name}.log")
  run = sorted(p.name for p in LOGS.glob(f"*_{run_name}"))[-1]
  return run, round((time.time() - t0) / 60, 1)


def ep_len(log):
  v = re.findall(r"Mean episode length: ([0-9.]+)", Path(log).read_text(errors="ignore"))
  return float(v[-1]) if v else None


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--rounds", type=int, default=12)
  ap.add_argument("--iters", type=int, default=1500)
  ap.add_argument("--mode", choices=("llm", "rules"), default="llm",
                  help="llm: rules/templates only suggest, the agent decides each round (decisions/rNN.json); "
                       "rules: the rule-based adjust() changes the knobs (ablation baseline)")
  a = ap.parse_args()
  st = json.loads(STATE.read_text()) if STATE.exists() else {"rounds": [], "knobs": DEFAULT, "best": None}
  for key in ("weights", "prior", "terms", "tracking"):  # knobs added mid-run get their defaults (no KeyError)
    st["knobs"][key] = {**DEFAULT[key], **st["knobs"].get(key, {})}
  VID.mkdir(parents=True, exist_ok=True)
  import library as libm
  if CLIP not in libm.load().get("tasks", {}):  # step 0 for a new task: checklist from its reference + priors
    sh(f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; "
       f"python {HERE}/task_init.py {CLIP} {VAR} {FAMILY}", DL / f"task_init_{CLIP}.log")
  for rnd in range(len(st["rounds"]) + 1, a.rounds + 1):
    decision = apply_decision(st, rnd) if a.mode == "llm" else None
    if a.mode == "llm" and decision is None:
      print(f"=== round {rnd}: no decisions/r{rnd:02d}.json yet (LLM mode) -> stop", flush=True)
      break
    k = st["knobs"]
    init = (st["best"]["run"], st["best"]["ckpt"]) if st["best"] else None
    if decision and decision.get("init"):  # the decider picks the start (r10: best score != best policy)
      init = (decision["init"]["run"], decision["init"]["ckpt"])
    print(f"=== round {rnd} knobs {json.dumps(k)} init {init}", flush=True)
    run, mins = train(rnd, k, init, a.iters)
    cks = sorted((p.name for p in (LOGS / run).glob("model_*.pt")), key=lambda s: int(s[6:-3]))
    evals = []
    for ck in cks[-3:]:  # the last three saved checkpoints of the round
      r = evaluate(run, ck)
      if r:
        r = extra_metrics(r)
        r["ckpt"], r["score"] = ck, score(r)
        evals.append(r)
        v = Path(r["video"])
        if v.exists():
          sh(f"cp '{v}' '{VID}/r{rnd:02d}_{ck[:-3]}.mp4'")
    best_r = max(evals, key=lambda r: r["score"]) if evals else None
    critic_top, lib_changes, escalate = [], [], []
    if best_r:  # automatic multi-angle comparison + library checks (rl/flip_auto/critic.py, library.py)
      ev = LOGS / run / "eval"
      tag = f"auto_{best_r['ckpt'][:-3]}"
      sh(f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; "
         f"python {HERE}/critic.py {ev}/flip_{tag}_record.npz {DS}/labels_50fps.npz {ev}/flip_{tag}.mp4 "
         f"--round {rnd} --task {CLIP}", DL / f"critic_r{rnd:02d}.log")
      cj = ev / f"flip_{tag}_critic.json"
      if cj.exists():
        crit = json.loads(cj.read_text())
        critic_top = crit.get("issues", [])[:8]
        lib_changes, escalate = grow_library(crit, rnd, apply=(a.mode == "rules"))
        sh(f"cp '{ev}/flip_{tag}_critic.md' '{VID}/r{rnd:02d}_critic.md'; "
           f"cp '{ev}/flip_{tag}_critic_worst.jpg' '{VID}/r{rnd:02d}_critic_worst.jpg' 2>/dev/null")
    if a.mode == "rules":
      why = adjust(st["knobs"], best_r) if best_r else ["evaluation failed -> knobs unchanged"]
    else:  # LLM mode: the rules only suggest; the agent decides in decisions/r{rnd+1}.json
      import copy
      why = ["(suggestion) " + w for w in (adjust(copy.deepcopy(st["knobs"]), best_r) if best_r else [])]
    suspicious = bool(best_r and best_r["robot_airborne_s"] > 0.2 and best_r["pelvis_rise_m"] < 0.03)
    if best_r and not suspicious and (st["best"] is None or best_r["score"] > st["best"]["score"]):
      st["best"] = {"run": run, "ckpt": best_r["ckpt"], "score": best_r["score"], "round": rnd}
    st["rounds"].append({"round": rnd, "run": run, "minutes": mins, "knobs": k, "ep_len_end": ep_len(DL / f"train_flipauto_r{rnd:02d}.log"),
                         "evals": [{x: e[x] for x in ("ckpt", "score", "robot_rotation_deg", "robot_max_rotation_deg",
                                                      "robot_peak_pelvis_m", "pelvis_rise_m", "robot_airborne_s",
                                                      "landed_upright", "end_tilt_deg", "early_fall",
                                                      "plane_dev_max_deg", "plane_dev_mean_deg", "leg_asym_deg",
                                                      "leg_err_deg", "feet_dist_max_m", "feet_dist_touchdown_m",
                                                      "takeoff_offset_steps", "landing_offset_steps",
                                                      "flight_hip_err_rad", "rot_at_ref_landing_deg",
                                                      "ref_rot_at_landing_deg", "pelvis_min_after_landing_m",
                                                      "stand_stable", "stand_feet_d_end", "flight_hip_mean_rad",
                                                      "flight_knee_max_rad", "flight_knee_overfold_rad",
                                                      "knee_sep_min_m", "track_body_err_m", "track_joint_err",
                                                      "knee_sep_max_m", "flight_hip_roll_max_rad",
                                                      "flight_hip_yaw_max_rad", "stand_arm_vel_rms",
                                                      "stand_action_change", "stand_pelvis_speed",
                                                      "stand_torso_angvel")
                                                if x in e} for e in evals],
                         "adjust": why,
                         "critic_top": [{x: c[x] for x in ("severity", "kind", "what", "phase", "detail")}
                                        for c in critic_top],
                         "library_changes": lib_changes, "escalate": escalate, "mode": a.mode,
                         "decision": decision})
    STATE.write_text(json.dumps(st, indent=1))
    report(st)
    if a.mode == "llm":  # protocol step 1 runs automatically: frame sheets, robustness, quantitative report
      if best_r:
        sh(f"bash {HERE}/robust.sh {run} {best_r['ckpt']}", DL / f"robust_r{rnd:02d}.log")
      sh(f"source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab; cd {HERE}; "
         f"python analyze_round.py {rnd}; python quant_report.py {rnd}", DL / f"analysis_r{rnd:02d}.log")
    print(f"=== round {rnd} done: best {best_r and {x: best_r[x] for x in ('ckpt', 'score', 'robot_rotation_deg', 'pelvis_rise_m', 'robot_airborne_s', 'landed_upright')}} | {why}", flush=True)


def report(st):
  L = ["# Backflip auto harness (G1 EDU limits: knee 120 N.m)", "",
       "| round | train min | ep len | best ckpt | score | rotation deg (max) | pelvis rise m | airborne s | landed | out-of-plane deg (mean/max) | legs asym/err deg | feet dist max/touchdown m | adjustment |",
       "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
  for r in st["rounds"]:
    e = max(r["evals"], key=lambda x: x["score"]) if r["evals"] else None
    L.append(f"| {r['round']} | {r['minutes']} | {r['ep_len_end']} | {e and e['ckpt']} | {e and e['score']} | "
             f"{e and e['robot_rotation_deg']} ({e and e['robot_max_rotation_deg']}) | {e and e['pelvis_rise_m']} | "
             f"{e and e['robot_airborne_s']} | {e and e['landed_upright']} | "
             f"{e and e.get('plane_dev_mean_deg')}/{e and e.get('plane_dev_max_deg')} | "
             f"{e and e.get('leg_asym_deg')}/{e and e.get('leg_err_deg')} | "
             f"{e and e.get('feet_dist_max_m')}/{e and e.get('feet_dist_touchdown_m')} | {'; '.join(r['adjust'])} |")
  last = st["rounds"][-1] if st["rounds"] else None
  if last and last.get("decision"):
    d = last["decision"]
    L += ["", f"## LLM decision applied to round {last['round']}", "", f"reasoning: {d.get('reasoning', '')}", ""]
    L += [f"- priority: {x}" for x in d.get("priorities", [])]
    L += [f"- knob {k_}: {v}" for k_, v in d.get("knobs", {}).items()]
    L += [f"- library {k_}: weight {v}" for k_, v in d.get("library", {}).items()]
    L += [f"- code: {x}" for x in d.get("code_changes", [])]
  if last and last.get("library_changes"):
    L += ["", f"## Library changes after round {last['round']} (RSI on the checklist)", ""]
    L += [f"- {x}" for x in last["library_changes"]]
  if last and last.get("escalate"):
    L += ["", "## Needs a hand-written fix (template cannot express it or did not help)", "",
          "| check | severity | why | detail |", "|---|---|---|---|"]
    L += [f"| {e['check']} | {e['severity']} | {e['why']} | {e['detail']} |" for e in last["escalate"]]
  if last and last.get("critic_top"):
    L += ["", f"## Automatic critic, round {last['round']} (top issues, severity = measured / tolerance)", "",
          "| severity | kind | what | phase | detail |", "|---|---|---|---|---|"]
    L += [f"| {c['severity']} | {c['kind']} | {c['what']} | {c['phase']} | {c['detail']} |" for c in last["critic_top"]]
  L += ["", f"best so far: {st['best']}", "", "knobs now: `" + json.dumps(st["knobs"]) + "`"]
  (HERE / "REPORT.md").write_text("\n".join(L) + "\n")


if __name__ == "__main__":
  main()
