"""Self-iterating get-up training harness: train -> measure -> diagnose -> adjust reward knobs -> train again.

Each round warm-starts from the best run so far (a bad round is discarded, not built upon), trains ITERS
iterations of task Dance-Recovery-G1-auto with the round's knobs JSON, evaluates the final checkpoint with
rl/auto/metrics.py (falls + standing start), renders a 2x2 demo video, scores it against the targets, writes
rl/auto/REPORT.md and picks the next knobs with fixed, logged rules. Stops when all targets hold for two
consecutive rounds or after --rounds rounds.

Usage (any python3 with numpy, e.g. the gmr env):
  python harness.py --warm <run dir name> [--rounds 10] [--iters 1500] [--wait chain_getup_v7f.sh]
"""
import argparse
import json
import math
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

AUTO_DEFAULT_KNOBS = json.loads((Path(__file__).resolve().parent / "default_knobs.json").read_text())

HOME = Path.home()
RL = HOME / "dance_win" / "rl"
RUNS = HOME / "projects" / "dance" / "runs" / "logs" / "rsl_rl" / "g1_recovery"
STATE_DIR = HOME / "projects" / "dance_logs" / "auto"
REPORT = RL / "auto" / "REPORT.md"
VIDEOS = HOME / "dance_win" / "videos" / "getup"
MJ = ["bash", str(RL / "auto" / "run_mjlab.sh")]
TASK = "Dance-Recovery-G1-auto"

TARGETS = {  # name: (metric key, kind, bound)
  "success >= 0.97": ("success", ">=", 0.97),
  "time-to-stand median 2.0-3.5 s": ("t_stand_median", "in", (2.0, 3.5)),
  "every pose >= 1.8 s": ("t_stand_min_pose", ">=", 1.8),
  "feet distance while rising <= 0.45 m": ("feet_spread_median", "<=", 0.45),
  "squat match >= 0.5": ("squat_match_median", ">=", 0.5),
  "peak joint speed <= 10 rad/s": ("peak_joint_speed_median", "<=", 10.0),
  "torso tilt <= 3 deg": ("torso_tilt_median", "<=", 3.0),
  "standing template >= 0.9": ("template_median", ">=", 0.9),
  "keeps stance from a standing start (template >= 0.9)": ("stand_start_template", ">=", 0.9),
  "no balance stepping after standing (foot travel <= 0.05 m)": ("foot_travel_after_stand_median", "<=", 0.05),
  "no stomping while rising (touchdowns <= 4)": ("touchdowns_rising_median", "<=", 4.0),
  "no hard foot impacts (peak force <= 500 N)": ("peak_foot_force_median", "<=", 500.0),
  "still upper body after standing (sway <= 1.5 cm p-p)": ("sway_pp_cm_median", "<=", 1.5),
  "still upper body from a standing start (sway <= 1.5 cm p-p)": ("stand_start_sway_pp_cm", "<=", 1.5),
}


def log(msg):
  line = f"[harness {datetime.now():%m-%d %H:%M:%S}] {msg}"
  print(line, flush=True)
  with open(STATE_DIR / "harness.log", "a") as f:
    f.write(line + "\n")


def sh(cmd, logfile=None, env=None):
  """Run a command, stream to logfile, return exit code."""
  import os
  e = dict(os.environ)
  e.update(env or {})
  if logfile:
    with open(logfile, "a") as f:
      return subprocess.call(cmd, stdout=f, stderr=subprocess.STDOUT, env=e)
  return subprocess.call(cmd, env=e)


def train_with_watchdog(cmd, logfile, env, min_stand_up=8.0, grace_iters=300, bad_iters=200, poll_s=120):
  """Run training; every poll_s parse the log and stop it early if Episode_Reward/stand_up (~9.6 when the robots get
  up) stays below min_stand_up for bad_iters consecutive iterations after the first grace_iters - the signature of
  round 3 (sitting) and round 6 (squatting forever). Returns (exit code, reason or None)."""
  import os
  import re
  e = dict(os.environ)
  e.update(env)
  with open(logfile, "a") as f:
    p = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, env=e)
  first_it, low_since = None, None
  while p.poll() is None:
    time.sleep(poll_s)
    try:
      txt = Path(logfile).read_text(errors="ignore")
    except OSError:
      continue
    its = [int(x) for x in re.findall(r"Learning iteration (\d+)/", txt)]
    sus = [float(x) for x in re.findall(r"Episode_Reward/stand_up: ([-\d.]+)", txt)]
    if not its or len(sus) < 20:
      continue
    first_it = first_it or its[0]
    it = its[-1]
    su = sum(sus[-20:]) / 20  # mean over the last 20 iterations
    if it - first_it < grace_iters:
      continue
    if su < min_stand_up:
      low_since = low_since or it
      if it - low_since >= bad_iters:
        p.terminate()
        p.wait(timeout=60)
        return -1, f"stand_up reward {su:.2f} < {min_stand_up} for {it - low_since} iterations (it {it})"
    else:
      low_since = None
  return p.returncode, None


def busy(pattern):
  return subprocess.call(["pgrep", "-f", pattern], stdout=subprocess.DEVNULL) == 0


def latest_ckpt(run_dir):
  cks = sorted(run_dir.glob("model_*.pt"), key=lambda p: int(p.stem.split("_")[1]))
  return cks[-1] if cks else None


def check(m, key, kind, bound):
  v = m.get(key, float("nan"))
  if v is None or (isinstance(v, float) and math.isnan(v)):
    return False
  if kind == ">=":
    return v >= bound
  if kind == "<=":
    return v <= bound
  return bound[0] <= v <= bound[1]


def score(m):
  """Higher is better. Success dominates; the rest are normalised target violations."""
  def viol(key, kind, bound, scale):
    v = m.get(key, float("nan"))
    if v is None or math.isnan(v):
      return 1.0
    if kind == ">=":
      return max(0.0, bound - v) / scale
    if kind == "<=":
      return max(0.0, v - bound) / scale
    return (max(0.0, bound[0] - v) + max(0.0, v - bound[1])) / scale
  s = 10.0 * m.get("success", 0.0)
  s -= viol("t_stand_median", "in", (2.0, 3.5), 0.5)
  s -= viol("t_stand_min_pose", ">=", 1.8, 0.5)
  s -= viol("feet_spread_median", "<=", 0.45, 0.2)
  s -= viol("squat_match_median", ">=", 0.5, 0.3)
  s -= viol("peak_joint_speed_median", "<=", 10.0, 5.0)
  s -= viol("torso_tilt_median", "<=", 3.0, 5.0)
  s -= viol("template_median", ">=", 0.9, 0.2)
  s -= viol("stand_start_template", ">=", 0.9, 0.2)
  s -= viol("foot_travel_after_stand_median", "<=", 0.05, 0.1)
  s -= viol("touchdowns_rising_median", "<=", 4.0, 2.0)
  s -= viol("peak_foot_force_median", "<=", 500.0, 200.0)
  s -= viol("sway_pp_cm_median", "<=", 1.5, 1.5)
  s -= viol("stand_start_sway_pp_cm", "<=", 1.5, 1.5)
  return s


def adjust(k, m):
  """Rule-based knob update from the measured violations. Returns (new knobs, list of change descriptions)."""
  k = {**AUTO_DEFAULT_KNOBS, **k}  # knobs added after a round started get their defaults
  ch = []

  def mul(name, f, hi=None, why=""):
    """Scale a weight (penalties are negative); hi caps its magnitude."""
    old = k[name]
    new = old * f
    if hi is not None and abs(new) > hi:
      new = math.copysign(hi, new)
    k[name] = round(new, 6)
    ch.append(f"{name} {old} -> {k[name]} ({why})")

  def add(name, d, lo, hi, why=""):
    old = k[name]
    k[name] = round(min(hi, max(lo, old + d)), 4)
    ch.append(f"{name} {old} -> {k[name]} ({why})")

  if m["success"] < 0.95:
    why = f"success {m['success']:.2f} < 0.95: relax the constraints"
    mul("w_feet_spread", 0.7, why=why)
    mul("w_squat", 0.8, why=why)
    mul("w_rise_schedule", 0.8, why=why)
    mul("w_joint_speed_cap", 0.8, why=why)
    return k, ch
  t, tmin = m["t_stand_median"], m["t_stand_min_pose"]
  if (not math.isnan(t) and t < 2.0) or (not math.isnan(tmin) and tmin < 1.8):
    why = f"too fast (median {t:.2f} s, slowest pose min {tmin:.2f} s)"
    add("sched_duration", 0.3, 1.5, 3.5, why)
    add("t_gate", 0.3, 1.5, 3.5, why)
    mul("w_rise_schedule", 1.3, hi=3000, why=why)
  elif not math.isnan(t) and t > 3.5:
    why = f"too slow (median {t:.2f} s)"
    add("sched_duration", -0.3, 1.5, 3.5, why)
    add("t_gate", -0.3, 1.5, 3.5, why)
  if m["feet_spread_median"] > 0.45:
    why = f"feet {m['feet_spread_median']:.2f} m apart while rising"
    mul("w_feet_spread", 1.5, hi=500, why=why)
    if m["feet_spread_median"] > 0.6:
      add("feet_max_dist", -0.03, 0.30, 0.45, why)
  if m["squat_match_median"] < 0.5:
    why = f"squat match {m['squat_match_median']:.2f}"
    mul("w_squat", 1.5, hi=20, why=why)
    add("squat_prob", 0.05, 0.0, 0.3, why)
    if m["squat_match_median"] < 0.2:
      # far from the squat the exp kernel is ~0 and has no gradient (round 0: 0.01) -> widen it first
      add("squat_std", 0.04, 0.05, 0.25, why + ": widen the kernel so the reward has a gradient")
  if m["peak_joint_speed_median"] > 10.0:
    mul("w_joint_speed_cap", 1.5, hi=2.0, why=f"peak joint speed {m['peak_joint_speed_median']:.1f} rad/s")
  if m["torso_tilt_median"] > 3.0 or m["template_median"] < 0.9 or m.get("stand_start_template", 1.0) < 0.9:
    mul("w_stand_template", 1.3, hi=15, why=f"stance: tilt {m['torso_tilt_median']:.1f} deg, template "
        f"{m['template_median']:.2f}, from standing {m.get('stand_start_template', float('nan')):.2f}")
  if m.get("foot_travel_after_stand_median", 0.0) > 0.05:
    mul("w_feet_move_stand", 1.5, hi=200, why=f"balance stepping: feet travel "
        f"{m['foot_travel_after_stand_median']:.2f} m after standing")
  if m.get("touchdowns_rising_median", 0.0) > 4.0:
    mul("w_feet_move_rise", 1.5, hi=20, why=f"stomping: {m['touchdowns_rising_median']:.1f} touchdowns while rising")
  if m.get("peak_foot_force_median", 0.0) > 500.0:
    mul("w_foot_impact", 1.5, hi=30, why=f"foot impacts {m['peak_foot_force_median']:.0f} N")
  sway = max(m.get("sway_pp_cm_median", 0.0), m.get("stand_start_sway_pp_cm", 0.0))
  if sway > 1.5:
    why = (f"upper-body sway {m.get('sway_pp_cm_median', float('nan')):.1f} cm (from falls) / "
           f"{m.get('stand_start_sway_pp_cm', float('nan')):.1f} cm (standing start) peak-to-peak")
    # round 6d+: stillness is a positive bonus (penalty versions were escaped by not standing)
    mul("w_still_bonus", 1.3, hi=15, why=why)
  return k, ch


def report_round(r, knobs, m, ok, sc, best, changes, video, run_dir):
  first = not REPORT.exists()
  with open(REPORT, "a") as f:
    if first:
      f.write("# Get-up self-iteration report (rl/auto/harness.py)\n\nTargets: " +
              "; ".join(TARGETS) + "\n\n")
    f.write(f"## Round {r}  ({datetime.now():%Y-%m-%d %H:%M})  score {sc:.2f}"
            f"{'  **best so far**' if best else ''}\n\n")
    f.write(f"- run `{run_dir.name}`, checkpoint `{m['ckpt'].split('/')[-1]}`; video `videos/getup/{video}`\n")
    pp = ", ".join(f"{k} {v['t_stand']:.2f} s ({v['success']:.0%})" for k, v in m["per_pose"].items())
    f.write(f"- success {m['success']:.0%}, time-to-stand median {m['t_stand_median']:.2f} s; per pose: {pp}\n")
    f.write(f"- feet distance while rising {m['feet_spread_median']:.2f} m, squat match {m['squat_match_median']:.2f}, "
            f"peak joint speed {m['peak_joint_speed_median']:.1f} rad/s (accel {m['peak_joint_accel_median']:.0f}), "
            f"peak pelvis |vz| {m['peak_vz_median']:.2f} m/s, max pelvis z {m['max_pelvis_z']:.2f} m\n")
    f.write(f"- stance: torso tilt {m['torso_tilt_median']:.1f} deg, pelvis tilt {m['pelvis_tilt_median']:.1f} deg, "
            f"template {m['template_median']:.2f}; from a standing start: template "
            f"{m.get('stand_start_template', float('nan')):.2f}, still standing "
            f"{m.get('stand_start_still_standing', float('nan')):.0%}\n")
    f.write(f"- feet: {m.get('touchdowns_rising_median', float('nan')):.1f} touchdowns while rising, "
            f"{m.get('touchdowns_after_stand_median', float('nan')):.1f} after standing, foot travel after standing "
            f"{m.get('foot_travel_after_stand_median', float('nan')):.2f} m, peak foot force "
            f"{m.get('peak_foot_force_median', float('nan')):.0f} N\n")
    f.write(f"- upper-body sway after standing: {m.get('sway_pp_cm_median', float('nan')):.1f} cm p-p from falls, "
            f"{m.get('stand_start_sway_pp_cm', float('nan')):.1f} cm from a standing start; torso angular speed RMS "
            f"{m.get('torso_angv_rms_median', float('nan')):.2f} / {m.get('stand_start_torso_angv_rms', float('nan')):.2f} rad/s\n")
    f.write("- targets: " + ", ".join(f"{'OK' if v else 'X'} {n}" for n, v in ok.items()) + "\n")
    f.write(f"- knobs: `{json.dumps(knobs)}`\n")
    if changes:
      f.write("- next round changes:\n" + "".join(f"  - {c}\n" for c in changes))
    f.write("\n")


def main():
  ap = argparse.ArgumentParser()
  ap.add_argument("--warm", required=True, help="run dir name to start from")
  ap.add_argument("--rounds", type=int, default=10)
  ap.add_argument("--iters", type=int, default=1500)
  ap.add_argument("--envs", type=int, default=2048)
  ap.add_argument("--lr", type=float, default=3e-4, help="initial learning rate of each warm-started round")
  ap.add_argument("--wait", default="", help="pgrep -f pattern to wait for before starting (e.g. a running chain)")
  a = ap.parse_args()
  STATE_DIR.mkdir(parents=True, exist_ok=True)
  state_f = STATE_DIR / "state.json"
  state = json.loads(state_f.read_text()) if state_f.exists() else \
      {"round": 0, "knobs": dict(AUTO_DEFAULT_KNOBS), "best": None, "warm": a.warm, "met_streak": 0}
  if a.wait:
    while busy(a.wait):
      time.sleep(30)
    log(f"'{a.wait}' finished")
  while state["round"] < a.rounds:
    r = state["round"]
    ov = STATE_DIR / "override_warm.json"
    if ov.exists():
      # human override (e.g. the user picked a checkpoint by eye): continue from it and make this lineage the
      # reference - earlier rounds no longer count as "best", so the harness does not revert away from it
      o = json.loads(ov.read_text())
      state["warm"], state["warm_ckpt"], state["best"] = o["warm"], o["warm_ckpt"], None
      ov.rename(STATE_DIR / f"override_warm_used_r{r:02d}.json")
      log(f"round {r}: override -> warm start {o['warm']}/{o['warm_ckpt']} ({o.get('reason', '')}); best reset")
      with open(REPORT, "a") as f:
        f.write(f"## Override before round {r}: continue from `{o['warm']}/{o['warm_ckpt']}` "
                f"({o.get('reason', '')}); earlier rounds no longer count as best\n\n")
    rd = STATE_DIR / f"r{r:02d}"
    rd.mkdir(exist_ok=True)
    knobs_f = rd / "knobs.json"
    knobs_f.write_text(json.dumps(state["knobs"], indent=1))
    env = {"GETUP_TASK": TASK, "GETUP_KNOBS": str(knobs_f)}
    run = f"auto_r{r:02d}"
    log(f"round {r}: warm start {state['warm']}, knobs {json.dumps(state['knobs'])}")
    warm_args = ["--agent.load-run", state["warm"]]
    if state.get("warm_ckpt"):
      warm_args += ["--agent.load-checkpoint", state["warm_ckpt"]]
    # warm-start fine-tuning: lr 3e-4 instead of the 1e-3 the adaptive schedule restarts from (the decayed lr is not
    # in the checkpoint) and no random initial episode clocks - with lr 1e-3 the round-5 policy collapsed within
    # ~50 iterations every time (rounds 6-7, A/B tests); with 3e-4 it kept standing (test E2, 2026-10-21)
    env = dict(env, GETUP_NO_RANDOM_EP_LEN="1")
    code, why = train_with_watchdog(MJ + ["python", str(RL / "train_getup.py"), "--", "--env.scene.num-envs",
                                          str(a.envs), "--agent.max-iterations", str(a.iters), "--agent.run-name",
                                          run, "--agent.logger", "wandb", "--agent.wandb-project", "g1_dance",
                                          "--agent.algorithm.learning-rate", str(a.lr),
                                          "--agent.resume", "True"] + warm_args, rd / "train.log", env)
    run_dirs = sorted(RUNS.glob(f"*_{run}"))
    ck = latest_ckpt(run_dirs[-1]) if run_dirs else None
    if why:
      log(f"round {r}: watchdog stopped training: {why}; discarding the round, relaxing knobs from the best round")
      with open(REPORT, "a") as f:
        f.write(f"## Round {r} stopped by the watchdog ({datetime.now():%Y-%m-%d %H:%M}): {why}\n\n")
      base = state["best"]["knobs"] if state["best"] else state["knobs"]
      state["knobs"], _ = adjust(base, {"success": 0.0})
      state["round"] += 1
      state_f.write_text(json.dumps(state, indent=1))
      continue
    if code != 0 or ck is None:
      log(f"round {r}: training failed (exit {code}); see {rd / 'train.log'}; retrying from best with relaxed knobs")
      state["knobs"], _ = adjust(state["knobs"], {"success": 0.0})
      state["round"] += 1
      state_f.write_text(json.dumps(state, indent=1))
      continue
    log(f"round {r}: trained -> {ck}")
    # checkpoint selection inside the round: behaviours that no reward term pins down (e.g. stepping) drift between
    # checkpoints (v7f: foot travel after standing 0.25 / 0.45 / 0.19 / 0.28 m at 19500 / 20000 / 20550 / 21098),
    # so the last checkpoint is not necessarily the best -> measure the last three 500-iteration marks
    last = int(ck.stem.split("_")[1])
    cands = [c for c in (ck, run_dirs[-1] / f"model_{last - last % 500}.pt",
                         run_dirs[-1] / f"model_{last - last % 500 - 500}.pt") if c.exists()]
    cands = list(dict.fromkeys(cands))
    m, sc = None, -1e9
    for i, c in enumerate(cands):
      fo, so = rd / f"fall_{i}.json", rd / f"stand_{i}.json"
      sh(MJ + ["python", str(RL / "auto" / "metrics.py"), "--ckpt", str(c), "--out", str(fo)],
         logfile=rd / "eval.log", env=env)
      sh(MJ + ["python", str(RL / "auto" / "metrics.py"), "--ckpt", str(c), "--out", str(so), "--stand_start"],
         logfile=rd / "eval.log", env=env)
      try:
        mi = json.loads(fo.read_text())
        mi.update(json.loads(so.read_text()))
      except Exception as e:  # noqa: BLE001
        log(f"round {r}: evaluation of {c.name} failed ({e})")
        continue
      mi["t_stand_min_pose"] = min((v["t_stand"] for v in mi["per_pose"].values()
                                    if not math.isnan(v["t_stand"])), default=float("nan"))
      si = score(mi)
      log(f"round {r}: candidate {c.name} score {si:.2f}")
      if si > sc:
        m, sc, ck = mi, si, c
    if m is None:
      log(f"round {r}: evaluation failed; see {rd / 'eval.log'}")
      state["round"] += 1
      state_f.write_text(json.dumps(state, indent=1))
      continue
    (rd / "fall.json").write_text(json.dumps({k: v for k, v in m.items() if not k.startswith("stand_start")}))
    (rd / "stand.json").write_text(json.dumps({k: v for k, v in m.items() if k.startswith("stand_start")}))
    log(f"round {r}: selected {ck.name}")
    video = f"auto_r{r:02d}.mp4"
    sh(MJ + ["bash", str(RL / "demo_getup.sh"), str(ck), video[:-4],
             f"G1 get-up auto round {r} (lying -> squat -> stand)"], logfile=rd / "video.log", env=env)
    ok = {n: check(m, *spec) for n, spec in TARGETS.items()}
    is_best = state["best"] is None or sc > state["best"]["score"]
    if is_best:
      state["best"] = {"round": r, "score": sc, "run": run_dirs[-1].name, "ckpt": str(ck), "knobs": state["knobs"]}
    new_knobs, changes = adjust(state["knobs"], m)
    report_round(r, state["knobs"], m, ok, sc, is_best, changes if not all(ok.values()) else [], video,
                 run_dirs[-1])
    (rd / "metrics.json").write_text(json.dumps(m, indent=1))
    log(f"round {r}: score {sc:.2f} (best {state['best']['score']:.2f} @ round {state['best']['round']}), "
        f"targets met {sum(ok.values())}/{len(ok)}, video {VIDEOS / video}")
    state["met_streak"] = state["met_streak"] + 1 if all(ok.values()) else 0
    # next round: from the best run; the knobs evolve from the CURRENT round's measurement if it is the best,
    # otherwise from the best round's knobs (a worse round's changes are discarded)
    state["warm"] = state["best"]["run"]
    state["warm_ckpt"] = Path(state["best"]["ckpt"]).name
    if not is_best:
      new_knobs, changes = adjust(state["best"]["knobs"], json.loads(
          (STATE_DIR / f"r{state['best']['round']:02d}" / "metrics.json").read_text()))
      # nudge differently than last time to avoid repeating a rejected step: halve every change
      best_k = {**AUTO_DEFAULT_KNOBS, **state["best"]["knobs"]}  # knobs added later get their defaults
      for key in new_knobs:
        old, new = best_k.get(key), new_knobs[key]
        if isinstance(old, (int, float)) and isinstance(new, (int, float)) and not isinstance(old, bool):
          new_knobs[key] = round(old + 0.5 * (new - old), 4)
      log(f"round {r} was worse than round {state['best']['round']}: next round restarts from it with half steps")
    state["knobs"] = new_knobs
    state["round"] += 1
    state_f.write_text(json.dumps(state, indent=1))
    if state["met_streak"] >= 2:
      log("all targets met in two consecutive rounds - stopping")
      break
  b = state["best"]
  if b:
    pol = HOME / "dance_win" / "policies" / "getup_auto_best"
    pol.mkdir(parents=True, exist_ok=True)
    subprocess.call(["cp", b["ckpt"], str(pol / "policy.pt")])
    (pol / "SOURCE.txt").write_text(json.dumps(b, indent=1))
    log(f"done. best round {b['round']} score {b['score']:.2f}: {b['ckpt']} -> {pol}")


if __name__ == "__main__":
  main()
