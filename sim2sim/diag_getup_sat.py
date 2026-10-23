"""Get-up sim2sim, physics root cause #2 + capability boundary: force-SATURATED position actuators under implicitfast.

mujoco_warp 3.5.0 (_src/derivative.py, _qderiv_actuator_passive_vel) puts the actuator velocity derivative (biasprm[2] =
-kv of a position actuator) into qDeriv for EVERY actuator, without looking at actuator_forcelimited / the clamp. If
C MuJoCo drops that term for a clamped actuator, the two implicitfast integrators differ exactly when actuators
saturate (pushes, impacts, large tracking errors), although the applied forces are identical.

This script (unitree_rl_mjlab env, GPU + CPU) measures that, using 128 envs (seed 0, balanced fallen poses: env i has
pose i % 4 and push level LEVELS[i // 32]):
  1. qDeriv check: at the pushed state, diagonal of the velocity derivative at every actuated dof, native (d.qDeriv
     after mj_step) vs mujoco_warp (derivative.deriv_smooth_vel called on the same state), vs -(dof_damping + kv).
  2. single 5 ms substep, same state + warm start + ctrl in both sims, at the reset state, at the pushed state and
     1 / 5 policy steps later: nominal; native with a WARP-STYLE derivative (saturated actuators: force limit + ctrl
     limit switched off and ctrl shifted so that the applied force is exactly the clamped force -> same forces, but
     -kv stays in qDeriv); Euler integrator in both; force limits off in both.
  3. closed loop after a push: mjlab rolls 200 policy steps (4 s; all envs standing), the state of every env is pushed
     (joint pos +-0.3 rad (clipped to range), root lin vel +-1 m/s, root ang vel +-2 rad/s, joint vel N(0, 1.5) rad/s,
     all scaled by the env's push level), then mjlab continues to 10 s; native (nominal and warp-style derivative)
     runs from the SAME pushed state (+ warm start + last action) for the same 300 steps.
  4. get-up phase (no push, envs 0..31): native nominal vs native warp-style derivative from the reset states,
     divergence vs mjlab during the first 4 s, and how often actuators saturate.
-> out/getup_satdiag.json (read by native_getup.py report)
Usage: bash diag_getup_sat.sh
"""
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from native_getup import KNOBS, OUT, POLICY, ROOT, TASK, CpuActor, NativeG1, balanced_lying_reset, kin  # noqa: E402

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(ROOT / "rl"))
os.environ["GETUP_TASK"] = TASK
os.environ["GETUP_KNOBS"] = str(KNOBS)

import mujoco  # noqa: E402
import torch  # noqa: E402
import warp as wp  # noqa: E402
from mujoco_warp._src import derivative as wderiv  # noqa: E402
from tensordict import TensorDict  # noqa: E402

import getup  # noqa: E402,F401
import mjlab.tasks  # noqa: E402,F401
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.managers.event_manager import EventTermCfg  # noqa: E402
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls  # noqa: E402

DEV = "cuda:0"
LEVELS = [0.0, 0.5, 1.0, 2.0]
PER = 32
N = PER * len(LEVELS)
PUSH, T = 200, 500
level = np.array([LEVELS[i // PER] for i in range(N)])

cfg = load_env_cfg(TASK, play=True)
cfg.seed = 0
cfg.scene.num_envs = N
for k in [k for k, v in cfg.events.items() if v.mode in ("startup", "interval")]:
  cfg.events.pop(k)
cfg.events["reset_base"] = EventTermCfg(func=balanced_lying_reset, mode="reset", params=dict(cfg.events["reset_base"].params))
env = ManagerBasedRlEnv(cfg=cfg, device=DEV)
agent = load_rl_cfg(TASK)
venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent), device=DEV)
runner.load(str(POLICY), load_cfg={"actor": True}, strict=True, map_location=DEV)
policy = runner.get_inference_policy(device=DEV)
sd, wd, wm = env.sim.data, env.sim.wp_data, env.sim.wp_model
nat = NativeG1()
m = nat.m
actor = CpuActor()
dt = float(env.step_dt)
h = float(m.opt.timestep)

# ---- actuator model (all G1 actuators: dyn none, fixed gain kp, affine bias [0, -kp, -kv]) ----
assert np.all(m.actuator_dyntype == mujoco.mjtDyn.mjDYN_NONE)
assert np.all(m.actuator_gaintype == mujoco.mjtGain.mjGAIN_FIXED)
assert np.all(m.actuator_biastype == mujoco.mjtBias.mjBIAS_AFFINE)
G = m.actuator_gainprm[:, 0].copy()
B0, B1, B2 = (m.actuator_biasprm[:, i].copy() for i in range(3))
FR = m.actuator_forcerange.copy()
FL = m.actuator_forcelimited.copy()
CR = m.actuator_ctrlrange.copy()
CL = m.actuator_ctrllimited.copy()
act_dof = np.array([m.jnt_dofadr[int(m.actuator_trnid[i, 0])] for i in range(m.nu)])
gear = m.actuator_gear[:, 0].copy()
assert np.allclose(gear, 1.0)
jnt_actfrc = bool(np.any(m.jnt_actfrclimited)) if hasattr(m, "jnt_actfrclimited") else None
act_params = {"kp_min_max": [float(G.min()), float(G.max())], "kv_min_max": [float(-B2.max()), float(-B2.min())],
              "dof_damping_actuated_min_max": [float(m.dof_damping[act_dof].min()), float(m.dof_damping[act_dof].max())],
              "forcerange_abs_min_max": [float(np.abs(FR).min()), float(np.abs(FR).max())],
              "n_forcelimited": int(FL.sum()), "n_ctrllimited": int(CL.sum()), "joint_actfrclimited_any": jnt_actfrc,
              "integrator": int(m.opt.integrator), "warp_is_sparse": bool(wm.is_sparse)}
print("[sat] actuator params:", act_params, flush=True)


def raw_force(ctrl, length, vel):
  c = np.where(CL.astype(bool), np.clip(ctrl, CR[:, 0], CR[:, 1]), ctrl)
  return G * c + B0 + B1 * length + B2 * vel


def saturated(d):
  raw = raw_force(d.ctrl, d.actuator_length, d.actuator_velocity)
  return FL.astype(bool) & ((raw < FR[:, 0]) | (raw > FR[:, 1])), raw


def substep_warpstyle(ctrl):
  """One mj_step with the same applied forces, but saturated actuators keep -kv in qDeriv (as mujoco_warp does)."""
  d = nat.d
  d.ctrl[:] = ctrl
  mujoco.mj_forward(m, d)
  sat, raw = saturated(d)
  if sat.any():
    F = np.clip(raw[sat], FR[sat, 0], FR[sat, 1])
    c2 = np.array(ctrl, dtype=np.float64)
    c2[sat] = (F - B0[sat] - B1[sat] * d.actuator_length[sat] - B2[sat] * d.actuator_velocity[sat]) / G[sat]
    m.actuator_forcelimited[sat] = 0
    m.actuator_ctrllimited[sat] = 0
    d.ctrl[:] = c2
    mujoco.mj_step(m, d)
    m.actuator_forcelimited[:] = FL
    m.actuator_ctrllimited[:] = CL
  else:
    mujoco.mj_step(m, d)
  return int(sat.sum())


def native_step(act, warpstyle):
  ctrl = nat.ctrl_from_action(act)
  nsat = 0
  if warpstyle:
    for _ in range(nat.decim):
      nsat += substep_warpstyle(ctrl)
    mujoco.mj_forward(m, nat.d)
  else:
    nat.step(act)
  return nsat


def snap():
  return (sd.qpos.cpu().numpy().astype(np.float64), sd.qvel.cpu().numpy().astype(np.float64),
          sd.qacc_warmstart.cpu().numpy().astype(np.float64))


def write(q, v, w):
  sd.qpos[:] = torch.as_tensor(q, dtype=sd.qpos.dtype, device=DEV)
  sd.qvel[:] = torch.as_tensor(v, dtype=sd.qvel.dtype, device=DEV)
  sd.qacc_warmstart[:] = torch.as_tensor(w, dtype=sd.qacc_warmstart.dtype, device=DEV)


# ---------------------------------------------------------------------------------------------------------------
# mjlab rollout with a push at step PUSH
# ---------------------------------------------------------------------------------------------------------------
rng = np.random.default_rng(0)
env.reset()
obs = venv.get_observations()
origins = env.scene.env_origins.cpu().numpy().astype(np.float64)
pose = env._getup_pose.cpu().numpy().copy()
reset_state = snap()
states = {"reset (t=0)": (*reset_state, None)}
qlog = np.zeros((T, N, m.nq))
vlog = np.zeros((T, N, m.nv))
t0 = time.time()
for s in range(T):
  if s == PUSH:
    q, v, w = snap()
    jadr, jr = m.jnt_qposadr[1:], m.jnt_range[1:]
    dq = rng.uniform(-0.3, 0.3, (N, len(jadr))) * level[:, None]
    q[:, jadr] = np.clip(q[:, jadr] + dq, np.minimum(jr[:, 0] + 0.02, q[:, jadr]), np.maximum(jr[:, 1] - 0.02, q[:, jadr]))
    v[:, 0:3] += rng.uniform(-1.0, 1.0, (N, 3)) * level[:, None]
    v[:, 3:6] += rng.uniform(-2.0, 2.0, (N, 3)) * level[:, None]
    v[:, 6:] += rng.normal(0.0, 1.5, (N, m.nv - 6)) * level[:, None]
    write(q, v, w)
    env.sim.forward()
    obs = TensorDict(env.observation_manager.compute(update_history=True), batch_size=[N])
    push_state = snap()
    push_last = env.action_manager.action.cpu().numpy().astype(np.float64)
  pre = snap()
  with torch.no_grad():
    act = policy(obs)
  if s == PUSH:
    states["pushed (t=4.00 s)"] = (*pre, act.clone())
  elif s == PUSH + 1:
    states["push + 1 policy step"] = (*pre, act.clone())
  elif s == PUSH + 5:
    states["push + 5 policy steps"] = (*pre, act.clone())
  elif s == 0:
    states["reset (t=0)"] = (*pre, act.clone())
  with torch.no_grad():
    obs, _, _, _ = venv.step(act)
  q, v, _ = snap()
  q[:, 0:2] -= origins[:, 0:2]
  qlog[s], vlog[s] = q, v
print(f"[sat] mjlab rollout done ({time.time() - t0:.0f}s)", flush=True)

# ---------------------------------------------------------------------------------------------------------------
# native closed loops: after the push (all envs) and the get-up phase (envs 0..31, no push)
# ---------------------------------------------------------------------------------------------------------------
pq, pv, pw = push_state
pq_local = pq.copy()


def run_native(q0, v0, w0, last0, steps, warpstyle):
  ql = np.zeros((steps, m.nq))
  nsat = 0
  nat.set_state(q0, v0, w0)
  last = np.array(last0, dtype=np.float64)
  for s in range(steps):
    a = actor(nat.obs(last))[0]
    nsat += native_step(a, warpstyle)
    last = a
    ql[s] = nat.d.qpos
  return ql, nsat


t0 = time.time()
after = {"mjlab": qlog[PUSH:]}
sat_count = {}
for tag, ws in (("native", False), ("native_warpstyle_deriv", True)):
  lg = np.zeros((T - PUSH, N, m.nq))
  ns = np.zeros(N)
  for e in range(N):
    lg[:, e], ns[e] = run_native(pq[e], pv[e], pw[e], push_last[e], T - PUSH, ws)
  lg[:, :, 0:2] -= origins[None, :, 0:2]
  after[tag] = lg
  if ws:
    sat_count["after_push_saturated_actuator_substeps_per_env"] = {
      str(L): float(ns[level == L].mean()) for L in LEVELS}
  print(f"[sat] native {tag} after push done ({time.time() - t0:.0f}s)", flush=True)

GU = PER  # get-up phase: envs 0..31 (push level 0, 8 per pose)
rq, rv, rw = reset_state
getup = {"mjlab": qlog[:PUSH, :GU]}
sat_sub_first = None
for tag, ws in (("native", False), ("native_warpstyle_deriv", True)):
  lg = np.zeros((PUSH, GU, m.nq))
  ns = np.zeros(GU)
  for e in range(GU):
    lg[:, e], ns[e] = run_native(rq[e], rv[e], rw[e], np.zeros(29), PUSH, ws)
  lg[:, :, 0:2] -= origins[None, :GU, 0:2]
  getup[tag] = lg
  if ws:
    sat_count["getup_phase_saturated_actuator_substeps_per_env_mean"] = float(ns.mean())
    sat_count["getup_phase_actuator_substeps_per_env"] = int(PUSH * nat.decim * m.nu)
print(f"[sat] native get-up phase done ({time.time() - t0:.0f}s)", flush=True)


def div_table(ref, lg, idx, at_steps):
  jr = np.sqrt(np.mean((ref[:, idx, 7:] - lg[:, idx, 7:]) ** 2, axis=2))
  rp = np.linalg.norm(ref[:, idx, 0:3] - lg[:, idx, 0:3], axis=2)
  return [{"t_s": round((s + 1) * dt, 3), "joint_rms_median_rad": float(np.median(jr[s])),
           "joint_rms_max_rad": float(jr[s].max()), "root_pos_max_m": float(rp[s].max())} for s in at_steps]


def outcome(lg):
  z, tilt = kin(nat, lg)
  ok = (z > 0.70) & (tilt < 15.0)
  return {"recovered": ok[-50:].all(axis=0), "fell": z.min(axis=0) < 0.5, "lost_ok": ~ok.all(axis=0)}


AT = [0, 4, 24, 49, 149, T - PUSH - 1]
outs = {tag: outcome(lg) for tag, lg in after.items()}
closed = {}
for L in LEVELS:
  idx = np.where(level == L)[0]
  row = {"n": int(len(idx))}
  for tag in after:
    row[tag] = {k: float(v[idx].mean()) for k, v in outs[tag].items()}
  for tag in ("native", "native_warpstyle_deriv"):
    a_, b_ = outs["mjlab"]["recovered"][idx], outs[tag]["recovered"][idx]
    row[f"recovered_agreement_mjlab_vs_{tag}"] = {"both": int((a_ & b_).sum()), "mjlab_only": int((a_ & ~b_).sum()),
                                                   f"{tag}_only": int((~a_ & b_).sum()), "neither": int((~a_ & ~b_).sum())}
    row[f"divergence_{tag}_vs_mjlab"] = div_table(after["mjlab"], after[tag], idx, AT)
  closed[str(L)] = row
  print(f"[sat] push level {L}: " + ", ".join(f"{t} recovered {row[t]['recovered']:.0%} fell {row[t]['fell']:.0%}"
                                             for t in after), flush=True)
getup_div = {tag: div_table(getup["mjlab"], getup[tag], np.arange(GU), [4, 24, 49, 99, PUSH - 1])
             for tag in ("native", "native_warpstyle_deriv")}

# ---------------------------------------------------------------------------------------------------------------
# qDeriv diagonal check at the pushed state (envs with push level > 0)
# ---------------------------------------------------------------------------------------------------------------
q, v, w, act = states["pushed (t=4.00 s)"]
write(q, v, w)
env.action_manager.process_action(act)
env.action_manager.apply_action()
env.scene.write_data_to_sim()
env.sim.forward()
qderiv_check = None
if True:
  out = wp.zeros(wd.qM.shape, dtype=wp.float32, device=wd.qM.device)
  wderiv.deriv_smooth_vel(wm, wd, out)
  wp.synchronize()
  qD_raw = (wd.qM.numpy().astype(np.float64) - out.numpy().astype(np.float64)) / h  # out = qM - h * qDeriv
  if wm.is_sparse:  # (nworld, 1, nM), element k <-> dofs (qM_fullm_i[k], qM_fullm_j[k]); keep the diagonal
    qi, qj = wm.qM_fullm_i.numpy(), wm.qM_fullm_j.numpy()
    qD_warp = np.zeros((N, m.nv, m.nv))
    for k in np.where(qi == qj)[0]:
      qD_warp[:, qi[k], qi[k]] = qD_raw[:, 0, k]
  else:
    qD_warp = qD_raw
  a_np = act.cpu().numpy().astype(np.float64)
  Dsrc = m if hasattr(m, "D_rownnz") else nat.d
  rows = {"sat": {"native": [], "warp": [], "expect_with_kv": [], "expect_without_kv": []},
          "unsat": {"native": [], "warp": [], "expect_with_kv": [], "expect_without_kv": []}}
  for e in np.where(level > 0)[0]:
    nat.set_state(q[e], v[e], w[e])
    nat.d.ctrl[:] = nat.ctrl_from_action(a_np[e])
    mujoco.mj_forward(m, nat.d)
    sat, _ = saturated(nat.d)
    mujoco.mj_step(m, nat.d)  # implicitfast: d.qDeriv = derivative at the pre-step state
    for i in range(m.nu):
      j = int(act_dof[i])
      adr, nnz = int(Dsrc.D_rowadr[j]), int(Dsrc.D_rownnz[j])
      cols = list(Dsrc.D_colind[adr:adr + nnz])
      dn = float(nat.d.qDeriv[adr + cols.index(j)])
      r = rows["sat" if sat[i] else "unsat"]
      r["native"].append(dn)
      r["warp"].append(float(qD_warp[e, j, j]))
      r["expect_with_kv"].append(float(B2[i] - m.dof_damping[j]))
      r["expect_without_kv"].append(float(-m.dof_damping[j]))
  qderiv_check = {}
  for k, r in rows.items():
    a = {kk: np.array(vv) for kk, vv in r.items()}
    if not len(a["native"]):
      qderiv_check[k] = {"n": 0}
      continue
    tol = lambda x, y: np.abs(x - y) <= 1e-3 * np.maximum(1.0, np.abs(y))  # noqa: E731
    qderiv_check[k] = {
      "n": int(len(a["native"])),
      "native_matches_with_kv_frac": float(tol(a["native"], a["expect_with_kv"]).mean()),
      "native_matches_without_kv_frac": float(tol(a["native"], a["expect_without_kv"]).mean()),
      "warp_matches_with_kv_frac": float(tol(a["warp"], a["expect_with_kv"]).mean()),
      "warp_matches_without_kv_frac": float(tol(a["warp"], a["expect_without_kv"]).mean()),
      "max_abs_native_minus_warp": float(np.abs(a["native"] - a["warp"]).max())}
print("[sat] qDeriv diagonal check:", qderiv_check, flush=True)

# ---------------------------------------------------------------------------------------------------------------
# single substep comparisons
# ---------------------------------------------------------------------------------------------------------------
GROUPS = {"all envs": np.arange(N)} | {f"push level {L}": np.where(level == L)[0] for L in LEVELS if L > 0}


def warp_substep(q, v, w, act):
  write(q, v, w)
  env.action_manager.process_action(act)
  env.action_manager.apply_action()
  env.scene.write_data_to_sim()
  env.sim.step()
  return sd.qvel.cpu().numpy().astype(np.float64)


def native_substep(q, v, w, a, warpstyle):
  nat.set_state(q, v, w)
  ctrl = nat.ctrl_from_action(a)
  nat.d.ctrl[:] = ctrl
  mujoco.mj_forward(m, nat.d)
  sat, _ = saturated(nat.d)
  if warpstyle:
    nat.set_state(q, v, w)
    substep_warpstyle(ctrl)
  else:
    mujoco.mj_step(m, nat.d)
  return nat.d.qvel.copy(), sat


def compare(variant, native_variants):
  res = {}
  for sname, (q, v, w, act) in states.items():
    v1 = warp_substep(q, v, w, act)
    a_np = act.cpu().numpy().astype(np.float64)
    for nv_name, ws in native_variants:
      dv, worst_sat, nsat = np.zeros(N), np.zeros(N, bool), np.zeros(N)
      for e in range(N):
        vn, sat = native_substep(q[e], v[e], w[e], a_np[e], ws)
        dd = np.abs(vn - v1[e])
        dv[e] = dd.max()
        j = int(dd.argmax())
        worst_sat[e] = bool(np.any(sat[act_dof == j]))
        nsat[e] = sat.sum()
      name = variant if nv_name is None else nv_name
      res.setdefault(name, {})[sname] = {
        g: {"dqvel_median": float(np.median(dv[idx])), "dqvel_max": float(dv[idx].max()),
            "saturated_actuators_per_env_median": float(np.median(nsat[idx])),
            "worst_dof_actuator_saturated_frac": float(worst_sat[idx].mean())}
        for g, idx in GROUPS.items() if sname != "reset (t=0)" or g == "all envs"}
      g = "push level 1.0" if sname != "reset (t=0)" else "all envs"
      print(f"[sat] {name:58s} {sname:24s} {g}: median {res[name][sname][g]['dqvel_median']:.2e} max "
            f"{res[name][sname][g]['dqvel_max']:.2e} worst-dof saturated {res[name][sname][g]['worst_dof_actuator_saturated_frac']:.0%}",
            flush=True)
  return res


substep = {}
substep |= compare("nominal (implicitfast, force limits)",
                   [(None, False), ("native with warp-style derivative (saturated actuators keep -kv)", True)])
# sanity: with Euler (derivative unused) the warp-style native step must equal the nominal native step
m.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
q, v, w, act = states["pushed (t=4.00 s)"]
a_np = act.cpu().numpy().astype(np.float64)
sanity = max(float(np.abs(native_substep(q[e], v[e], w[e], a_np[e], True)[0]
                          - native_substep(q[e], v[e], w[e], a_np[e], False)[0]).max()) for e in range(N))
print(f"[sat] sanity, Euler: |warp-style native - nominal native| max {sanity:.2e}", flush=True)
wm.opt.integrator = int(mujoco.mjtIntegrator.mjINT_EULER)
env.sim.create_graph()
substep |= compare("Euler integrator in both (force limits on)", [(None, False)])
m.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
wm.opt.integrator = int(mujoco.mjtIntegrator.mjINT_IMPLICITFAST)
m.actuator_forcelimited[:] = 0
wm.actuator_forcelimited.assign(np.zeros(m.nu, dtype=bool))
env.sim.create_graph()
substep |= compare("actuator force limits off in both (implicitfast)", [(None, False)])
m.actuator_forcelimited[:] = FL

summary = {
  "what": "actuator saturation x implicitfast velocity derivative; seed 0, 128 envs (pose = env % 4, push level = "
          f"{LEVELS}[env // 32]), push at policy step {PUSH} (t = 4 s): joint pos U(+-0.3) rad (clipped to range - 0.02), "
          "root lin vel U(+-1) m/s, root ang vel U(+-2) rad/s, joint vel N(0, 1.5) rad/s, each times the push level",
  "warp_source": "mujoco_warp 3.5.0 _src/derivative.py _qderiv_actuator_passive_vel: vel = biasprm[2] (+ gain terms) "
                 "for every actuator, actuator_forcelimited is not read",
  "warp_qderiv_storage": "sparse (diagonal elements via qM_fullm_i == qM_fullm_j)" if wm.is_sparse else "dense",
  "actuator_params": act_params, "qderiv_diag_check_pushed_state": qderiv_check,
  "warpstyle_vs_nominal_native_under_euler_max_dqvel": sanity,
  "single_substep": substep, "closed_loop_after_push": closed, "getup_phase_divergence_vs_mjlab": getup_div,
  "saturation_counts": sat_count,
  "outcome_definitions": "recovered = pelvis z > 0.70 m and torso tilt < 15 deg in each of the last 50 policy steps "
                         "(last 1 s of the 10 s episode); fell = pelvis z < 0.5 m at any time after the push; lost_ok = "
                         "the stand condition failed at least once after the push",
}
(OUT / "getup_satdiag.json").write_text(json.dumps(summary, indent=1))
np.savez_compressed(OUT / "getup_satdiag_traj.npz", level=level, pose=pose, push_step=PUSH,
                    **{f"after_{k}": v for k, v in after.items()}, **{f"getup_{k}": v for k, v in getup.items()})
print("[sat] wrote", OUT / "getup_satdiag.json", flush=True)
