"""Sim2sim exam for any tracking skill (first user: cartwheel_2), judged by the SAME success rule as the harness
robustness evaluation (rl/eval_flip_robust.py, v2), so a sim2sim number is directly comparable with robust.*:
  |rotation of the torso about its dominant axis| >= 0.9 x the reference's own AND over the post_s hold window
  (reference final frame held, rl/mimic_generic.hold_pad_npz): torso tilt < 30 deg, pelvis z > 0.6 m, and pelvis
  drift < 0.5 m (v2; nominal uses v1 0.3 m, as robust.sh does).
Native MuJoCo (CPU, float64) on models/<model>.mjb exported by export_flip_model.py (--hand-friction for hand-supported
skills) with the native observation / action / actor of native_dance.py and the rollout, start jitter, pushes and
model variants of native_flip.py (all imported, unchanged).
Writes results_skill_<policy>_<tag>.json and, with --eval-dir, <eval-dir>/sim2sim_<ckpt>.json ({"success": {...}}),
which rl/flip_auto/stop_criteria.py reads as the sim2sim.* gates (nominal, delay20 = scenario lat20).
Usage: python native_skill.py --policy cartwheel_r11 --model cartwheel [--runs 100] [--scenarios nominal,lat20]
  [--eval-dir <run>/eval --ckpt model_12500] [--xml models/cartwheel.xml --tag mj316]"""
import argparse
import json
import sys
import tempfile
import time
from pathlib import Path

import mujoco
import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.append(str(HERE.parent / "rl"))  # appended: import only, never shadows
from native_dance import ANCHOR, G1_ASSETS, Motion, Policy, load_xml_model  # noqa: E402
from native_flip import PUSH_HI, PUSH_LO, SEED, FlipG1, flip_rollout, jitter_state, rot_curve  # noqa: E402
from mimic_generic import hold_pad_npz  # noqa: E402

POST_S = 5.0
# name, description, kwargs; push windows are set per clip from its labels (first phase / hold window)
SCENARIOS = [
  ("nominal", "no perturbation", {}),
  ("lat20", "position targets delayed by 4 physics steps = 20 ms (fixed lag, DelayedActuator semantics)", {"lag": 4}),
  ("lat40", "position targets delayed by 8 physics steps = 40 ms", {"lag": 8}),
  ("fric0.5", "foot geom friction 0.5 (nominal 0.6)", {"friction": 0.5}),
  ("fric1.0", "foot geom friction 1.0 (nominal 0.6)", {"friction": 1.0}),
  ("kp085", "PD stiffness x0.85 on every actuator (damping unchanged)", {"kp_scale": 0.85}),
  ("push_pre", "one random root-velocity push (half the training range) during the first labelled phase", {"push": "pre"}),
  ("push_post", "one random root-velocity push during the first 2 s of the hold window", {"push": "post"}),
]


def tilt_of(q):
  w, x, y, z = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
  return np.degrees(np.arccos(np.clip(1 - 2 * (x * x + y * y), -1, 1)))


def judge(g, traj, n_ref, ref_rot, nominal):
  """rl/eval_flip_robust.py on one native trajectory (traj[k] = state after k policy steps)."""
  d = mujoco.MjData(g.m)
  a = g.bid[ANCHOR]
  tq = []
  for q in traj:
    d.qpos[:] = q
    mujoco.mj_kinematics(g.m, d)
    tq.append(d.xquat[a].copy())
  tq = np.array(tq)[1:-1]  # robust eval records after each of T-2 steps
  pel = traj[1:-1, g.rq + 2]
  pxy = traj[1:-1, g.rq:g.rq + 2]
  rot = abs(float(rot_curve(tq)[-1]))
  nr = n_ref - 2
  tilt = float(tilt_of(tq[nr:]).max())
  pmin = float(pel[nr:].min())
  drift = float(np.linalg.norm(pxy[-1] - pxy[nr]))
  base = rot >= 0.9 * ref_rot and tilt < 30 and pmin > 0.6
  ok1 = base and drift < 0.3
  return dict(success=bool(ok1 if nominal else base and drift < 0.5), success_v1=bool(ok1), rotation_deg=round(rot, 1),
              hold_tilt_max_deg=round(tilt, 1), hold_pelvis_min_m=round(pmin, 3), hold_drift_m=round(drift, 3),
              fell=bool(pmin < 0.4))


def main(a):
  if a.xml:
    xml = Path(a.xml) if Path(a.xml).is_absolute() else HERE / a.xml
    m, src = load_xml_model(xml, a.assets), str(xml)
  else:
    m, src = mujoco.MjModel.from_binary_path(str(HERE / "models" / f"{a.model}.mjb")), f"models/{a.model}.mjb"
  info = json.loads((HERE / "models" / f"{a.model}_info.json").read_text())
  g = FlipG1(m, info)
  pdir = HERE.parent / "policies" / a.policy
  pol = Policy(pdir / "policy.pt")
  padded = Path(tempfile.gettempdir()) / f"skill_{a.policy}_{a.tag}_post.npz"  # per tag: parallel processes
  n_ref, n_all = hold_pad_npz(pdir / "reference_motion.npz", padded, POST_S)
  mot = Motion(padded)
  labels = dict(np.load(pdir / "labels_50fps.npz"))
  ph = labels["phase"]
  first_end = int(np.argmax(ph != ph[0]))  # end of the first labelled phase (the initial stand)
  dt = float(info["step_dt"])
  T = mot.T
  # the reference's own rotation, measured like the robust eval (anchor quat over the same T-2 steps)
  ref_rot = abs(float(rot_curve(mot.bq[1:T - 1, g.mot_idx[ANCHOR]])[-1]))
  sel = [s for s in SCENARIOS if not a.scenarios or s[0] in a.scenarios.split(",")]
  out = dict(policy=a.policy, model=src, mujoco=mujoco.__version__, hand_friction=info.get("hand_friction"),
             knee_limit=info.get("knee_limit"), runs_per_scenario=a.runs, frames_reference=n_ref, frames_with_hold=n_all,
             ref_rotation_deg=round(ref_rot, 1), success_rule="rl/eval_flip_robust.py v2 (nominal: v1)",
             start_jitter=dict(root_xy_m=a.jit_xy, roll_pitch_rad=a.jit_rp, yaw_rad=a.jit_yaw, joint_pos_rad=a.jit_q),
             push_range_lo=PUSH_LO.tolist(), push_range_hi=PUSH_HI.tolist(), scenarios=[])
  print(f"[{a.tag}] {a.policy} on {src} (MuJoCo {mujoco.__version__}, hand friction {info.get('hand_friction')}): "
        f"{n_ref} + {n_all - n_ref} hold frames, reference rotation {ref_rot:.1f} deg", flush=True)
  t0 = time.perf_counter()
  for name, desc, kw in sel:
    g.set_variant(friction=kw.get("friction"), kp_scale=kw.get("kp_scale"))
    rows, exact = [], None
    for i in range(a.runs + 1):  # run 0 = exact reference start
      rng = np.random.default_rng([SEED, i])
      init = None if i == 0 else jitter_state(g, *g.ref_state(mot, 0), rng, a)
      pushes = None
      if kw.get("push"):
        prng = np.random.default_rng([SEED, 7, i])
        lo, hi = (min(10, first_end - 1), max(first_end, 11)) if kw["push"] == "pre" else (n_ref, n_ref + 100)
        pushes = {int(prng.integers(lo, hi)): prng.uniform(PUSH_LO, PUSH_HI)}
      r = flip_rollout(g, pol, mot, 0, T - 1, lag=kw.get("lag", 0), pushes=pushes, init=init)
      met = judge(g, r["traj"], n_ref, ref_rot, name == "nominal")
      met["knee_torque_max_Nm"] = round(float(np.abs(r["knee_force"]).max()), 2)
      if i == 0:
        exact = met
      else:
        rows.append(met)
    g.set_variant()
    arr = lambda k: np.array([r[k] for r in rows], float)
    pct = lambda x: [round(float(v), 3) for v in np.percentile(x, [5, 50, 95])]
    s = dict(name=name, description=desc, runs=len(rows), success_rate=round(float(arr("success").mean()), 3),
             success_rate_v1=round(float(arr("success_v1").mean()), 3), falls=int(arr("fell").sum()),
             rotation_deg_p5_50_95=pct(arr("rotation_deg")), hold_tilt_max_deg_p5_50_95=pct(arr("hold_tilt_max_deg")),
             hold_drift_m_p5_50_95=pct(arr("hold_drift_m")), knee_torque_max_Nm=float(arr("knee_torque_max_Nm").max()),
             exact_start=exact)
    out["scenarios"].append(s)
    print(f"[{a.tag}] {name:9s} success {s['success_rate']:.3f} (v1 {s['success_rate_v1']:.3f}, {len(rows)} runs) "
          f"falls {s['falls']} rot p5/50/95 {s['rotation_deg_p5_50_95']} hold tilt {s['hold_tilt_max_deg_p5_50_95']} "
          f"drift {s['hold_drift_m_p5_50_95']} | exact start {exact['success']} | knee max {s['knee_torque_max_Nm']} N.m "
          f"({time.perf_counter() - t0:.0f} s)", flush=True)
  out["wall_s"] = round(time.perf_counter() - t0, 1)
  (HERE / f"results_skill_{a.policy}_{a.tag}.json").write_text(json.dumps(out, indent=1))
  if a.eval_dir:
    gate = {"nominal": "nominal", "delay20": "lat20"}
    succ = {s["name"]: s["success_rate"] for s in out["scenarios"]}
    succ.update({k: succ[v] for k, v in gate.items() if v in succ})
    p = Path(a.eval_dir) / f"sim2sim_{a.ckpt}.json"
    p.write_text(json.dumps({"success": succ, "source": f"sim2sim/results_skill_{a.policy}_{a.tag}.json",
                             "model": src, "mujoco": mujoco.__version__}, indent=1))
    print(f"[{a.tag}] wrote {p}", flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--policy", required=True)
  ap.add_argument("--model", default="cartwheel", help="models/<model>.mjb + <model>_info.json")
  ap.add_argument("--xml", default=None)
  ap.add_argument("--assets", default=str(G1_ASSETS))
  ap.add_argument("--tag", default="mj350")
  ap.add_argument("--runs", type=int, default=100)
  ap.add_argument("--scenarios", default=None)
  ap.add_argument("--eval-dir", default=None)
  ap.add_argument("--ckpt", default=None)
  ap.add_argument("--jit_xy", type=float, default=0.02)
  ap.add_argument("--jit_rp", type=float, default=0.02)
  ap.add_argument("--jit_yaw", type=float, default=0.05)
  ap.add_argument("--jit_q", type=float, default=0.02)
  main(ap.parse_args())
