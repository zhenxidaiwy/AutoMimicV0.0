"""Step 1 of a round's decision (protocol: quantify -> LLM analysis -> solution -> train): the full quantitative report
of round K, written BEFORE the decider looks for causes. Output: analysis/rKK_quant.md
Sections: A metrics vs previous round, B per-phase deviations (critic angles), C library checks + effective signal of
every active template fix (exp(-err/std): ~0 means the fix gives no gradient), D uncovered deviations, E stand after
landing, F training-config audit (reward terms the training actually ran vs the code's defaults), G frame sheets to
review. Usage (unitree_rl_mjlab env): python quant_report.py K"""
import json
import math
import re
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent))
import critic  # noqa: E402
import library as libm  # noqa: E402

H = Path.home()
LOGS = H / "projects/dance/runs/logs/rsl_rl/g1_tracking"
DS = H / "projects/dance/dataset/backflip_3"
k = int(sys.argv[1])
st = json.loads((HERE / "state.json").read_text())
rd = st["rounds"][k - 1]
best = max(rd["evals"], key=lambda e: e.get("score", -1))
prev = max(st["rounds"][k - 2]["evals"], key=lambda e: e.get("score", -1)) if k > 1 else {}
ck = best["ckpt"][:-3]
ev = LOGS / rd["run"] / "eval"
R = np.load(ev / f"flip_auto_{ck}_record.npz", allow_pickle=True)
L = np.load(DS / "labels_50fps.npz")
V = critic.measure(R, L)
M = [f"# Round {k} - quantitative report (step 1, before any diagnosis)", "",
     f"run `{rd['run']}`, best checkpoint `{best['ckpt']}` (score {best.get('score')}), "
     f"evaluated: " + ", ".join(f"{e['ckpt']} {e.get('score')}" for e in rd["evals"]), ""]

# A metrics
M += ["## A. Evaluation metrics (best checkpoint) vs previous round", "", "| metric | this | previous | change |",
      "|---|---|---|---|"]
for key, v in best.items():
  if key in ("ckpt",) or isinstance(v, (list, dict)):
    continue
  p = prev.get(key, "-")
  ch = f"{v - p:+.3g}" if isinstance(v, (int, float)) and isinstance(p, (int, float)) and not isinstance(v, bool) else ""
  M.append(f"| {key} | {v} | {p} | {ch} |")

# A2 robustness (eval_flip_robust.py via robust.sh: 256 envs per scenario)
rp = ev / f"robust_{ck}.json"
if rp.exists():
  M += ["", "## A2. Robustness (success = rotation >= 330, upright, pelvis > 0.6 m at the end)", "",
        "| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |", "|---|---|---|---|---|"]
  M += [f"| {r['scenario']} | {r['success']} | {r['fell']} | {r['rotation_deg_p5_50_95']} | {r['end_tilt_deg_p5_50_95']} |"
        for r in json.loads(rp.read_text())]

# B per phase
M += ["", "## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)", ""]
rows = [(p, kd, t, v / tol, d) for (kd, t, p), (v, tol, fr, d) in V.items()]
for ph in dict.fromkeys(r[0] for r in rows):
  rs = sorted([r for r in rows if r[0] == ph], key=lambda r: -r[3])
  nfail = sum(r[3] > 1 for r in rs)
  M += [f"**{ph}**: {nfail} of {len(rs)} measurements beyond tolerance", ""]
  M += [f"- {r[3]:.1f} {r[1]}:{r[2]} - {r[4]}" for r in rs[:6] if r[3] > 1] + [""]

# C library + effective signal
lib = libm.load()
TASK = next(iter(lib.get("tasks", {})), "backflip_3")
TCHK = libm.task_checks(lib, TASK)  # measured checks of this task (generic / family priors are copied in)
M += ["## C. Library checks that fail, with the effective signal of their fix", "",
      "signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);",
      "an active fix with signal < 0.05 gives the policy practically no gradient.", "",
      "| severity | check | fix | weight | std | signal |", "|---|---|---|---|---|---|"]
for c in TCHK:
  key = (c["kind"], c["target"], c["phase"])
  if key not in V:
    continue
  v, tol, fr, d = V[key]
  if v / tol <= 1:
    continue
  fix = c.get("fix") or {}
  std = fix.get("params", {}).get("std")
  sig = f"{math.exp(-v / std):.3g}" if std and fix.get("func") in ("dyn_joint", "dyn_sym", "dyn_body") else "-"
  M.append(f"| {v / tol:.1f} | {c['id']} | {fix.get('func', 'none')} | {c.get('weight', 0)} | {std} | {sig} |")
M[-0:] = M[-0:]
nfail = sum(1 for c in TCHK if (c["kind"], c["target"], c["phase"]) in V
            and V[(c["kind"], c["target"], c["phase"])][0] / V[(c["kind"], c["target"], c["phase"])][1] > 1)
M += ["", f"{nfail} of {len(TCHK)} checks of task {TASK} fail."]

# D uncovered
covered = {(c["kind"], c["target"], c["phase"]) for c in TCHK}
unc = sorted([r for r in rows if (r[1], r[2], r[0]) not in covered and r[3] > 2], key=lambda r: -r[3])
M += ["", f"## D. Deviations no check covers yet (severity > 2): {len(unc)}", ""]
M += [f"- {r[3]:.1f} {r[1]}:{r[2]}:{r[0]} - {r[4]}" for r in unc[:15]]

# E stand after landing
jn = [str(x) for x in R["joint_names"]]
q, qr, act, fz = R["q"], R["qr"], R["act"], R["foot_z"]
names = libm.phase_names({"phase_names": L["phase_names"], "phase": L["phase"][:len(q)]})
sa = np.array([i for i, n in enumerate(names) if n in ("settle", "stand_after")])
M += ["", "## E. After landing (settle + stand_after, robot vs reference)", ""]
if len(sa):
  wy = jn.index("waist_yaw_joint")
  M.append(f"- waist_yaw: robot max |{np.abs(q[sa, wy]).max():.2f}| rad (end {q[sa[-1], wy]:+.2f}), reference max "
           f"|{np.abs(qr[sa, wy]).max():.2f}|")
  arm = [i for i, n in enumerate(jn) if any(s in n for s in ("shoulder", "elbow"))]
  M.append(f"- arm joints mean |err| {np.degrees(np.abs(q[sa][:, arm] - qr[sa][:, arm]).mean()):.0f} deg; "
           f"worst: " + ", ".join(f"{jn[j].replace('_joint', '')} {np.degrees(np.abs(q[sa, j] - qr[sa, j]).mean()):.0f}"
                                  for j in sorted(arm, key=lambda j: -np.abs(q[sa, j] - qr[sa, j]).mean())[:4]))
  M.append(f"- action change mean {np.abs(np.diff(act[sa], axis=0)).mean():.3f} (quiet < 0.05)")
  dt = float(R["dt"])
  acc = np.abs(np.diff(q[sa], 2, axis=0)).mean(0) / dt ** 2
  M.append("- joint acceleration mean (rad/s^2), worst: " + ", ".join(
    f"{jn[j].replace('_joint', '')} {acc[j]:.0f}" for j in np.argsort(-acc)[:4]))
  M.append(f"- feet off the floor (> 6 cm): left {int((fz[sa, 0] > 0.06).sum())}, right {int((fz[sa, 1] > 0.06).sum())} "
           f"of {len(sa)} steps")
  # per label segment (r11: the walk-off started exactly at the settle -> stand switch, where three terms stopped)
  bn = [str(x) for x in R["body_names"]]
  pel = R["bp"][:, bn.index("pelvis") if "pelvis" in bn else 0, :2]
  spd = np.r_[0, np.linalg.norm(np.diff(pel, axis=0), axis=-1) / dt]
  for seg in ("land", "settle", "stand_after"):
    ii = np.array([i for i, n in enumerate(names) if n == seg])
    if len(ii):
      M.append(f"- {seg} (steps {ii[0]}-{ii[-1]}): pelvis speed mean {spd[ii].mean():.2f} m/s, last {spd[ii[-1]]:.2f}; "
               f"drift {np.linalg.norm(pel[ii[-1]] - pel[ii[0]]):.2f} m")

# F training-config audit
log = H / "projects/dance_logs" / f"train_flipauto_r{k:02d}.log"
M += ["", "## F. Training-config audit (what the training actually ran)", ""]
if log.exists():
  txt = log.read_text(errors="ignore")
  terms = sorted(set(re.findall(r"Episode_Reward/(\w+):", txt)))
  code = (HERE.parent / "flip_rewards.py").read_text()
  wdef = re.search(r"WEIGHTS = \{(.*?)\}", code, re.S)
  expected = re.findall(r'"(flip_\w+)"', wdef.group(1)) if wdef else []
  missing = [t for t in expected if t not in terms]
  M.append(f"- {len(terms)} reward terms in the log; flip_* terms of the current code missing from training: "
           f"{missing or 'none'}")
  M.append(f"- root orientation term: {'flip_root_ori (replaced)' if 'flip_root_ori' in txt else 'motion_global_root_ori (global, NOT replaced)'}")
  for line in re.findall(r"\[train_dance\] (flip terminations: .*)", txt)[:1]:
    M.append(f"- {line[:300]}")
  M.append(f"- active library fixes: {len(re.findall(r'lib_[a-z_]+', (re.findall(r'library fixes: (.*)', txt) or [''])[0]))}, "
           f"decider terms: {len(set(re.findall(r'agent_r[0-9]+_[a-z_]+', txt)))}")

# F2 knob diff vs the previous round (r09 lesson: the rules had tightened the tracking curriculum after r08 and the
# decider believed it unchanged)
def flat(d, pre=""):
  out = {}
  for key, v in d.items():
    if isinstance(v, dict):
      out.update(flat(v, f"{pre}{key}."))
    else:
      out[f"{pre}{key}"] = json.dumps(v)[:120]
  return out


if k > 1:
  a_, b_ = flat(st["rounds"][k - 2].get("knobs", {})), flat(rd.get("knobs", {}))
  diff = [(key, a_.get(key, "-"), b_.get(key, "-")) for key in sorted(set(a_) | set(b_)) if a_.get(key) != b_.get(key)]
  M += ["", f"## F2. Knobs this round trained with vs round {k - 1} ({len(diff)} differences)", ""]
  M += [f"- {key}: {x} -> {y}" for key, x, y in diff]
  # the state's knobs of a round can have been mutated by the rules after it trained; the training logs are the truth
  def cfg_lines(r):
    p = H / "projects/dance_logs" / f"train_flipauto_r{r:02d}.log"
    if not p.exists():
      return {}
    out = {}
    for line in p.read_text(errors="ignore").splitlines():
      m = re.match(r".*?(\[train_dance\] [^:]+:|fidelity curriculum:)(.*)", line)
      if m and m.group(1) not in out:
        out[m.group(1)] = m.group(2).strip()
    return out
  ca, cb = cfg_lines(k - 1), cfg_lines(k)
  M += ["", "Training-log configuration lines that differ (ground truth):", ""]
  for key in sorted(set(ca) | set(cb)):
    if ca.get(key) != cb.get(key):
      M += [f"- {key} r{k - 1}: {ca.get(key, '-')[:260]}", f"  r{k}: {cb.get(key, '-')[:260]}"]

# G sheets
out = H / "dance_win/videos/backflip/auto" / f"r{k:02d}"
# S stop criteria (layered; also writes analysis/rKK_stop.json that the harness enforces)
try:
  import stop_criteria
  M += [""] + stop_criteria.markdown(stop_criteria.evaluate(k, TASK))
except Exception as e:  # the report must not fail because of the stop section
  M += ["", f"## S. Stop criteria: not evaluated ({type(e).__name__}: {e})"]

M += ["", "## G. Frame sheets to review (every step) - all must be reviewed before the decision", ""]
M += [f"- [ ] {p.name}" for p in sorted(out.glob("sheet_*.jpg"))]
dst = HERE / "analysis" / f"r{k:02d}_quant.md"
dst.parent.mkdir(exist_ok=True)
dst.write_text("\n".join(M) + "\n")
print("\n".join(M))
print("->", dst)
