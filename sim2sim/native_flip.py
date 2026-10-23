"""Sim2sim for the BACKFLIP tracking policies (Unitree-G1-Tracking-No-State-Estimation, 154-d actor obs, rsl_rl 5.0.1,
trained with the knee effort limit 120 N.m via rl/flip_rewards.set_knee_limit):
  policies/backflip_r14_fid2, backflip_r13_fid1, backflip_r12_clean
mjlab (mujoco_warp on GPU, float32) vs native MuJoCo (CPU, float64) running the exported runtime model models/flip.mjb
(sim2sim/export_flip_model.py) with the from-scratch re-implementation of observation / action / rsl_rl actor from
native_dance.py (imported, unchanged). Flip metrics reuse rl/eval_flip.cum_pitch (imported, unchanged).

--mode mjlab     (unitree_rl_mjlab env, CUDA, num_envs=1): play cfg, knee limit 120 applied exactly as in training, ALL
    randomisation off (startup events base_com / encoder_bias / foot_friction removed, push_robot already absent, RSI
    ranges zero), all terminations except time_out removed (a flip must not be cut). Rollout from frame 0 to frame T-1:
    at every step the mjlab state is copied into native MjData and (a) the 154-d obs is compared term by term, (b) the
    native policy is evaluated on mjlab's obs, (c) one policy step (4 x mj_step) is taken natively from the identical
    pre-step state / action / qacc_warmstart and next qpos/qvel + per-substep knee actuator forces are compared, (d) the
    contact geom-pair sets at that pre-step state are compared. Repeated off-nominal (pushes every 20 steps; action
    noise N(0, 0.3)), plus a single-substep test. Then closed loops from frame 0 in mjlab (twice: reproducibility) and
    natively, flip metrics for both from the recorded qpos with the same code, divergence at take-off / mid-flight /
    landing / end, side-by-side video.  -> results_flip_<P>.json, traj_flip_<P>.npz, videos/sim2sim/backflip_<rXX>_side_by_side.mp4
--mode mjlab_delay --lag L : mjlab with every actuator wrapped in DelayedActuatorCfg(min=max=L physics steps, hold 0)
    (the class add_action_delay uses in training, but with a fixed lag) -> checks that the native latency buffer
    reproduces mjlab's per-substep ctrl exactly, and compares the delayed closed loops.  -> results_flip_<P>_delay<L>.json
--mode native --tag T [--xml models/flip.xml]: pure mujoco + torch (e.g. gmr env, MuJoCo 3.16): closed loop from frame 0
    on the scene XML (+ meshes + runtime solver options), compared with the 3.5 trajectories. -> results_flip_<P>_<T>.json
--mode scenarios --tag T [--xml ...]: native perturbation suite (N runs per scenario, see SCENARIOS)
    -> results_flip_<P>_scen_<T>.json
--mode report: everything -> results_flip.json / results_flip.md
"""
import argparse
import json
import re
import sys
import time
from collections import Counter, deque
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.append(str(ROOT / "rl"))  # appended: import only, never shadows
from native_dance import (ANCHOR, DIMS, G1_ASSETS, TERMS, Motion, NativeG1, Policy, load_xml_model, qconj,  # noqa: E402
                          qmat, qmul, quat_angle, render_side_by_side, stat)

try:
  from eval_flip import cum_pitch  # rl/eval_flip.py (unchanged): unwrapped rotation about the dominant axis
except ImportError:  # pragma: no cover
  cum_pitch = None

VID_DIR = ROOT / "videos" / "sim2sim"
TASK = "Unitree-G1-Tracking-No-State-Estimation"
KNEE_LIMIT = 120.0
SEED = 2026
TAIL = 25  # last 0.5 s
SUCCESS_RULE = "|cumulative torso rotation| >= 330 deg AND over the last 0.5 s: torso tilt < 30 deg AND pelvis z > 0.6 m"
# native perturbation scenarios: (name, description, kwargs for flip_rollout / model edits)
SCENARIOS = [
  ("nominal", "no perturbation", {}),
  ("lat20", "position targets delayed by 4 physics steps = 20 ms (fixed lag, DelayedActuator semantics)", {"lag": 4}),
  ("lat40", "position targets delayed by 8 physics steps = 40 ms (fixed lag, DelayedActuator semantics)", {"lag": 8}),
  ("fric0.5", "foot geom friction 0.5 (nominal 0.6)", {"friction": 0.5}),
  ("fric1.0", "foot geom friction 1.0 (nominal 0.6)", {"friction": 1.0}),
  ("kp085", "PD stiffness x0.85 on every actuator (damping unchanged)", {"kp_scale": 0.85}),
  ("push_pre", "one random root-velocity push during the initial stand (step 10..60)", {"push": "pre"}),
  ("push_post", "one random root-velocity push during the final stand (step 156..162)", {"push": "post"}),
]
# half of the training push_robot ranges (x, y +-0.5, z +-0.2 m/s, roll/pitch +-0.52, yaw +-0.78 rad/s)
PUSH_LO = np.array([-0.25, -0.25, -0.1, -0.26, -0.26, -0.39])
PUSH_HI = -PUSH_LO


def short(pol):
  m = re.search(r"r\d+", pol)
  return m.group(0) if m else pol


def rot_curve(quats):
  q = np.asarray(quats, float)
  if cum_pitch is not None:
    return np.asarray(cum_pitch(q))
  inc = []  # same definition without scipy: per-step rotation vectors projected on their summed direction
  for a, b in zip(q[:-1], q[1:]):
    d = qmul(qconj(a), b)
    d = d if d[0] >= 0 else -d
    ang = 2 * np.arctan2(np.linalg.norm(d[1:]), d[0])
    inc.append(d[1:] / (np.linalg.norm(d[1:]) + 1e-12) * ang)
  inc = np.array(inc)
  ax = inc.sum(0)
  ax = ax / (np.linalg.norm(ax) + 1e-9)
  return np.degrees(np.concatenate([[0.0], np.cumsum(inc @ ax)]))


# --------------------------------------------------------------------------------------------- native flip helpers
class FlipG1(NativeG1):
  def __init__(self, m, info):
    super().__init__(m, info)
    self.knee_act = np.array([i for i in range(m.nu) if "knee" in m.actuator(i).name])
    rb = [b for b in range(m.nbody) if m.body(b).name.startswith("robot/")]
    self.robot_bodies = np.array(rb)
    self.robot_geom = np.isin(m.geom_bodyid, rb)
    self.foot_geoms = np.array([i for i in range(m.ngeom)
                                if re.match(r"^robot/(left|right)_foot[1-7]_collision$", m.geom(i).name or "")])
    self.nominal = dict(gain=m.actuator_gainprm.copy(), bias=m.actuator_biasprm.copy(), fric=m.geom_friction.copy())

  def knee_limit(self):
    return self.m.actuator_forcerange[self.knee_act].tolist()

  def set_variant(self, friction=None, kp_scale=None):
    m, n = self.m, self.nominal
    m.actuator_gainprm[:] = n["gain"]
    m.actuator_biasprm[:] = n["bias"]
    m.geom_friction[:] = n["fric"]
    if friction is not None:
      m.geom_friction[self.foot_geoms, 0] = friction
    if kp_scale is not None:
      m.actuator_gainprm[:, 0] *= kp_scale
      m.actuator_biasprm[:, 1] *= kp_scale

  def push(self, d, dv):
    """mjlab push_by_setting_velocity: root link velocity (world lin, world ang) += dv; free joint ang vel is local."""
    d.qvel[self.rv:self.rv + 3] += dv[:3]
    R = qmat(d.qpos[self.rq + 3:self.rq + 7])
    d.qvel[self.rv + 3:self.rv + 6] += R.T @ dv[3:]
    mujoco.mj_forward(self.m, d)


def jitter_state(g, q, v, rng, a):
  q, v = q.copy(), v.copy()
  q[g.rq:g.rq + 2] += rng.uniform(-a.jit_xy, a.jit_xy, 2)
  rpy = rng.uniform([-a.jit_rp, -a.jit_rp, -a.jit_yaw], [a.jit_rp, a.jit_rp, a.jit_yaw])
  ax = lambda i, ang: np.concatenate([[np.cos(ang / 2)], np.eye(3)[i] * np.sin(ang / 2)])
  dq = qmul(ax(2, rpy[2]), qmul(ax(1, rpy[1]), ax(0, rpy[0])))  # world-frame roll, pitch, then yaw
  q[g.rq + 3:g.rq + 7] = qmul(dq, q[g.rq + 3:g.rq + 7])
  v[g.rv:g.rv + 3] = qmat(dq) @ v[g.rv:g.rv + 3]
  q[g.qadr] = np.clip(q[g.qadr] + rng.uniform(-a.jit_q, a.jit_q, len(g.qadr)), g.soft_lo, g.soft_hi)
  return q, v


def flip_rollout(g, pol, mot, f, nsteps, lag=0, pushes=None, init=None, fill="first", warp_clamp=False):
  """warp_clamp=True emulates mujoco_warp's implicitfast: the effort limit is applied by the controller (ctrl chosen
  so that the PD force at the pre-step state equals the clamped force) with forcelimited switched off, so the actuator
  damping -kd stays in the implicit velocity derivative even while the force is clamped (MuJoCo C drops it for
  clamped actuators; measured in diag_flip_takeoff.py)."""
  if not warp_clamp:
    return _flip_rollout(g, pol, mot, f, nsteps, lag, pushes, init, fill, False)
  fl = g.m.actuator_forcelimited.copy()
  g.m.actuator_forcelimited[:] = 0
  try:
    return _flip_rollout(g, pol, mot, f, nsteps, lag, pushes, init, fill, True)
  finally:
    g.m.actuator_forcelimited[:] = fl


def _flip_rollout(g, pol, mot, f, nsteps, lag, pushes, init, fill, warp_clamp):
  """Native closed loop. lag = position-target delay in physics steps with mjlab DelayBuffer semantics (history
  backfilled with the first target after reset; the policy's last_action obs is the undelayed output, as with
  DelayedActuator). pushes = {step: dv(6)}. Returns qpos trajectory (traj[k] = after k policy steps) and per-substep
  knee actuator force / unclipped PD demand."""
  d = mujoco.MjData(g.m)
  q0, v0 = g.ref_state(mot, f) if init is None else init
  g.set_state(d, q0, v0)
  last, t, traj = np.zeros(29), f, [d.qpos.copy()]
  # fill: what the first `lag` substeps after the reset receive: "first" = the first policy target (DelayBuffer
  # backfill), "zeros" = ctrl 0 rad, "default" = default pose (action 0)
  pre = {"first": None, "zeros": np.zeros(29), "default": g.targets(np.zeros(29))}[fill]
  hist = deque(maxlen=lag + 1) if pre is None else deque([pre] * lag, maxlen=lag + 1)
  kf, kd, acts, ncon = [], [], [], []
  ka = g.knee_act
  kp, b1, b2 = g.m.actuator_gainprm[ka, 0], g.m.actuator_biasprm[ka, 1], g.m.actuator_biasprm[ka, 2]
  A = g.act
  akp, ab1, ab2 = g.m.actuator_gainprm[A, 0], g.m.actuator_biasprm[A, 1], g.m.actuator_biasprm[A, 2]
  alo, ahi = g.m.actuator_forcerange[A, 0], g.m.actuator_forcerange[A, 1]
  kpos = [int(np.where(A == i)[0][0]) for i in ka]  # knee actuators within joint order
  t0 = time.perf_counter()
  for k in range(nsteps):
    if pushes and k in pushes:
      g.push(d, pushes[k])
    a = pol(g.obs(d, mot, t, last))
    tgt = g.targets(a)
    for _ in range(g.decim):
      hist.append(tgt)
      if warp_clamp:
        q, qd = d.qpos[g.qadr], d.qvel[g.dadr]
        raw = akp * hist[0] + ab1 * q + ab2 * qd
        d.ctrl[A] = (np.clip(raw, alo, ahi) - ab1 * q - ab2 * qd) / akp
        kd.append(raw[kpos])
      else:
        d.ctrl[A] = hist[0]
      mujoco.mj_step(g.m, d)
      kf.append(d.actuator_force[ka].copy())  # force used in this step (computed at the pre-step state)
      if not warp_clamp:
        kd.append(kp * d.ctrl[ka] + b1 * d.actuator_length[ka] + b2 * d.actuator_velocity[ka])
      ncon.append(d.ncon)
    mujoco.mj_forward(g.m, d)
    last, t = a, t + 1
    acts.append(a)
    traj.append(d.qpos.copy())
  wall = time.perf_counter() - t0
  return dict(traj=np.array(traj), knee_force=np.array(kf), knee_demand=np.array(kd), actions=np.array(acts),
              ncon=np.array(ncon), wall=wall)


def contact_pairs(d):
  if d.ncon == 0:
    return np.zeros((0, 2), int)
  c = d.contact
  try:
    return np.asarray(c.geom, int).reshape(-1, 2)[:d.ncon]
  except AttributeError:
    return np.stack([np.asarray(c.geom1), np.asarray(c.geom2)], 1)[:d.ncon].astype(int)


def longest_run(mask):
  best, cur, end, best_end = 0, 0, -1, -1
  for i, x in enumerate(mask):
    cur = cur + 1 if x else 0
    if cur > best:
      best, best_end = cur, i
  return best, best_end - best + 1, best_end  # length, first index, last index


def flip_metrics(g, traj, dt, labels, knee_force=None, knee_demand=None, ncon=None):
  """Backflip metrics from recorded qpos (same code for both sims). traj[k] = state after k policy steps."""
  m = g.m
  d = mujoco.MjData(m)
  tq, pel, bmin, floor_c, tilt = [], [], [], [], []
  a = g.bid[ANCHOR]
  for q in traj:
    d.qpos[:] = q
    d.qvel[:] = 0
    mujoco.mj_fwdPosition(m, d)
    tq.append(d.xquat[a].copy())
    pel.append(float(q[g.rq + 2]))
    bmin.append(float(d.xpos[g.robot_bodies, 2].min()))
    gg = contact_pairs(d)
    floor_c.append(int(np.sum(g.robot_geom[gg[:, 0]] != g.robot_geom[gg[:, 1]])))  # robot <-> non-robot (floor)
    tilt.append(float(np.degrees(np.arccos(np.clip(d.xmat[a, 8], -1, 1)))))
  pel, bmin, floor_c, tilt = map(np.array, (pel, bmin, floor_c, tilt))
  rot = rot_curve(tq)
  n = len(traj)
  air_b = (bmin > 0.05) & (pel > 0.45)  # rl/eval_flip.py definition (every body origin > 5 cm, pelvis > 0.45 m)
  air_b[:16] = False  # eval_flip skips its first 15 records (= states 1..15): the reset drop is not a jump
  air_c = floor_c == 0
  air_c[:16] = False
  lb, _, _ = longest_run(air_b)
  lc, c0, c1 = longest_run(air_c)
  land = c1 + 1 if lc > 0 and c1 + 1 < n else None
  tail = slice(n - TAIL, n)
  ok = bool(abs(rot[-1]) >= 330 and (tilt[tail] < 30).all() and (pel[tail] > 0.6).all())
  pn = [str(x) for x in labels["phase_names"]]
  ph = labels["phase"]
  fl = np.where(ph == pn.index("flight"))[0]
  ref_takeoff, ref_land = int(fl[0]) + 1, int(fl[-1]) + 2  # state index k pairs with reference frame k-1
  pre = slice(0, min(ref_takeoff, n))
  res = dict(
    success=ok, rotation_deg=round(float(rot[-1]), 1), rotation_max_abs_deg=round(float(np.abs(rot).max()), 1),
    peak_pelvis_m=round(float(pel.max()), 3), airborne_s=round(lb * dt, 2), airborne_no_contact_s=round(lc * dt, 2),
    takeoff_step=int(c0) if lc else None, landing_step=land,
    takeoff_offset_steps=int(c0) - ref_takeoff if lc else None,
    landing_offset_steps=None if land is None else land - ref_land,
    landing_tilt_deg=None if land is None else round(float(tilt[land]), 1),
    landing_tilt_max_0p5s_deg=None if land is None else round(float(tilt[land:land + 25].max()), 1),
    pelvis_min_after_landing_m=None if land is None else round(float(pel[land:land + 25].min()), 3),
    end_tilt_deg=round(float(tilt[-1]), 1), tail_tilt_max_deg=round(float(tilt[tail].max()), 1),
    end_pelvis_m=round(float(pel[-1]), 3), tail_pelvis_min_m=round(float(pel[tail].min()), 3),
    fell=bool(pel[tail].min() < 0.4), early_fall=bool(((tilt[pre] > 60) & ~air_b[pre]).any()), steps=n - 1)
  if knee_force is not None and len(knee_force):
    kf = np.abs(np.asarray(knee_force))
    lim = np.abs(g.m.actuator_forcerange[g.knee_act, 1])
    res.update(knee_torque_max_Nm=round(float(kf.max()), 2),
               knee_torque_limit_Nm=lim.tolist(),
               knee_at_limit_frac=round(float((kf >= lim - 1e-3).any(1).mean()), 4),
               knee_torque_respects_limit=bool((kf <= lim + 1e-6).all()))
  if knee_demand is not None and len(knee_demand):
    res["knee_pd_demand_max_Nm"] = round(float(np.abs(knee_demand).max()), 1)
  if ncon is not None and len(ncon):
    res["ncon_max"] = int(np.max(ncon))
  curves = dict(rot=rot, pelvis=pel, tilt=tilt, floor_contacts=floor_c)
  return res, curves


def event_steps(labels, n):
  pn = [str(x) for x in labels["phase_names"]]
  ph = labels["phase"]
  fl = np.where(ph == pn.index("flight"))[0]
  ld = np.where(ph == pn.index("land"))[0]
  ev = [("takeoff", int(fl[0]) + 1), ("mid_flight", int((fl[0] + fl[-1]) // 2) + 1),
        ("landing", int(ld[0]) + 1), ("end", n - 1)]
  return [(k, min(v, n - 1)) for k, v in ev]


def event_divergence(g, ta, tb, labels, dt):
  n = min(len(ta), len(tb))
  d1, d2 = mujoco.MjData(g.m), mujoco.MjData(g.m)
  a = g.bid[ANCHOR]
  qa, qb = [], []
  for x, y in zip(ta[:n], tb[:n]):
    d1.qpos[:], d2.qpos[:] = x, y
    mujoco.mj_kinematics(g.m, d1)
    mujoco.mj_kinematics(g.m, d2)
    qa.append(d1.xquat[a].copy())
    qb.append(d2.xquat[a].copy())
  ra, rb = rot_curve(qa), rot_curve(qb)
  out = {}
  for name, k in event_steps(labels, n):
    dj = np.abs(ta[:k + 1][:, g.qadr] - tb[:k + 1][:, g.qadr])
    out[name] = dict(step=k, at_s=round(k * dt, 2), pelvis_pos_diff_m=round(float(np.linalg.norm(ta[k][:3] - tb[k][:3])), 4),
                     torso_ori_diff_deg=round(float(np.degrees(quat_angle(qa[k], qb[k]))), 2),
                     rotation_diff_deg=round(float(ra[k] - rb[k]), 2),
                     joint_max_abs_at_rad=round(float(dj[-1].max()), 4),
                     joint_rms_at_rad=round(float(np.sqrt(np.mean(dj[-1] ** 2))), 4),
                     joint_max_abs_upto_rad=round(float(dj.max()), 4),
                     bitwise_identical_upto=bool(np.array_equal(ta[:k + 1], tb[:k + 1])))
  first = np.where(np.any(ta[:n] != tb[:n], axis=1))[0]
  out["first_differing_step"] = int(first[0]) if len(first) else None
  out["curve_every_5_steps"] = [[k, round(float(np.linalg.norm(ta[k][:3] - tb[k][:3])), 4),
                                 round(float(np.abs(ta[k][g.qadr] - tb[k][g.qadr]).max()), 4)] for k in range(0, n, 5)]
  return out


def load_ctx(a, model=None):
  pdir = ROOT / "policies" / a.policy
  info = json.loads((HERE / "models" / "flip_info.json").read_text())
  m = model if model is not None else mujoco.MjModel.from_binary_path(str(HERE / "models" / "flip.mjb"))
  g = FlipG1(m, info)
  return pdir, info, g, Policy(pdir / "policy.pt"), Motion(pdir / "reference_motion.npz"), \
      dict(np.load(pdir / "labels_50fps.npz")), float(info["step_dt"])


# ---------------------------------------------------------------------------------------------------- mjlab mode
def build_mjlab(pdir, lag=None):
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  from dataclasses import asdict

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from flip_rewards import set_knee_limit  # rl/flip_rewards.py, import only
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  dev = "cuda:0" if torch.cuda.is_available() else "cpu"
  cfg = load_env_cfg(TASK, play=True)
  cfg.scene.num_envs = 1
  mc = cfg.commands["motion"]
  mc.motion_file = str(pdir / "reference_motion.npz")
  mc.pose_range, mc.velocity_range, mc.joint_position_range = {}, {}, (0.0, 0.0)
  removed_events = [k for k in ("base_com", "encoder_bias", "foot_friction", "push_robot")
                    if cfg.events.pop(k, None) is not None]
  removed_terms = [k for k in list(cfg.terminations) if k != "time_out"]
  for k in removed_terms:
    cfg.terminations.pop(k)
  art = cfg.scene.entities["robot"].articulation
  set_knee_limit(art, KNEE_LIMIT)  # exactly as train_dance.py --knee-limit 120
  if lag:
    from mjlab.actuator.delayed_actuator import DelayedActuatorCfg
    art.actuators = tuple(DelayedActuatorCfg(base_cfg=c, delay_target="position", delay_min_lag=lag,
                                             delay_max_lag=lag, delay_hold_prob=0.0) for c in art.actuators)
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent_cfg = load_rl_cfg(TASK)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(str(pdir / "policy.pt"), load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  cmd = env.command_manager.get_term("motion")
  start = [0]
  cmd.cfg.sampling_mode = "uniform"
  cmd._uniform_sampling = lambda env_ids: cmd.time_steps.__setitem__(env_ids, start[0])
  npy = lambda x: torch.as_tensor(x).detach().double().cpu().numpy()
  # record every physics substep (actuator force / ctrl / length / velocity) by wrapping sim.step on the instance
  rec = dict(on=False, f=[], ctrl=[], len=[], vel=[])
  orig_step = env.sim.step

  def step_rec(*args, **kw):
    out = orig_step(*args, **kw)
    if rec["on"]:
      dd = env.sim.data
      rec["f"].append(npy(dd.actuator_force[0]).copy())
      rec["ctrl"].append(npy(dd.ctrl[0]).copy())
      rec["len"].append(npy(dd.actuator_length[0]).copy())
      rec["vel"].append(npy(dd.actuator_velocity[0]).copy())
    return out

  env.sim.step = step_rec
  return dict(env=env, venv=venv, policy=policy, cmd=cmd, start=start, npy=npy, rec=rec, dev=dev,
              removed_events=removed_events, removed_terms=removed_terms,
              origin=env.scene.env_origins[0].double().cpu().numpy())


def mjlab_mode(a):
  pdir, info, g, pol, mot, labels, dt = load_ctx(a)
  E = build_mjlab(pdir)
  env, venv, policy, cmd, start, npy, rec = E["env"], E["venv"], E["policy"], E["cmd"], E["start"], E["npy"], E["rec"]
  origin, m, T = E["origin"], g.m, mot.T
  assert T == int(cmd.motion.time_step_total), (T, cmd.motion.time_step_total)
  ka = g.knee_act

  # ---- model checks (exported .mjb vs runtime mj_model; warp model vs nominal; knee limits in both)
  mrt = env.sim.mj_model
  fields = ("body_mass", "body_ipos", "body_inertia", "body_pos", "body_quat", "geom_friction", "geom_size",
            "geom_pos", "geom_solref", "geom_solimp", "geom_condim", "geom_contype", "geom_conaffinity", "dof_armature",
            "dof_damping", "dof_frictionloss", "jnt_range", "actuator_gainprm", "actuator_biasprm",
            "actuator_forcerange", "actuator_forcelimited", "actuator_trnid")
  mcheck = {"exported_vs_runtime_mj_model_max_abs": {}, "warp_model_vs_nominal_max_abs": {}}
  for f_ in fields:
    mcheck["exported_vs_runtime_mj_model_max_abs"][f_] = float(
      np.abs(np.asarray(getattr(m, f_), float) - np.asarray(getattr(mrt, f_), float)).max())
  for f_ in ("geom_friction", "body_ipos", "body_mass", "dof_armature", "actuator_gainprm", "actuator_biasprm",
             "actuator_forcerange"):
    try:
      w = npy(getattr(env.sim.model, f_))
      w = w.reshape((-1,) + np.asarray(getattr(m, f_)).shape)[0]
      mcheck["warp_model_vs_nominal_max_abs"][f_] = float(np.abs(w - np.asarray(getattr(m, f_), float)).max())
      if f_ == "actuator_forcerange":
        mcheck["warp_knee_forcerange"] = w[ka].tolist()
    except Exception as e:  # noqa: BLE001
      mcheck["warp_model_vs_nominal_max_abs"][f_] = repr(e)[:120]
  mcheck["mjb_knee_forcerange"] = g.knee_limit()
  mcheck["knee_actuators"] = [m.actuator(int(i)).name for i in ka]
  mcheck["opt"] = {k: [float(getattr(m.opt, k)), float(getattr(mrt.opt, k))] for k in
                   ("timestep", "iterations", "tolerance", "ls_iterations", "ls_tolerance", "impratio",
                    "integrator", "cone", "solver", "jacobian", "noslip_iterations")}
  try:
    mcheck["warp_nconmax_njmax"] = [int(getattr(env.sim.cfg, "nconmax", -1) or -1), int(getattr(env.sim.cfg, "njmax", -1) or -1)]
  except Exception:  # noqa: BLE001
    pass
  print("[model]", json.dumps(mcheck)[:2000], flush=True)

  tt = lambda x: torch.as_tensor(x, dtype=env.sim.data.qpos.dtype, device=env.sim.data.qpos.device)

  def mj_state():
    q, v = npy(env.sim.data.qpos[0]).copy(), npy(env.sim.data.qvel[0]).copy()
    q[:3] -= origin
    return q, v, npy(env.sim.data.qacc_warmstart[0]).copy()

  de = mujoco.MjData(m)
  eq = {"obs_term_max_abs": {t: 0.0 for t in TERMS}, "obs_checks": 0, "action_impl_max_abs": 0.0, "ctrl_max_abs": 0.0,
        "init_qpos_max_abs": 0.0, "init_qvel_max_abs": 0.0, "time_step_mismatch": 0,
        "reset_warmstart_max_abs_before_zeroing": 0.0, "substeps_per_policy_step": set()}
  dof_name = lambda i: mujoco.mj_id2name(m, mujoco.mjtObj.mjOBJ_JOINT, int(m.dof_jntid[i])).replace("robot/", "")

  def check_obs(t, into):
    q, v, _ = mj_state()
    g.set_state(de, q, v)
    nat = g.obs_terms(de, mot, t, npy(env.action_manager.action[0]))
    ref = npy(env.obs_buf["actor"][0])
    i = 0
    for name, dim, x in zip(TERMS, DIMS, nat):
      into[name] = max(into.get(name, 0.0), float(np.abs(x - ref[i:i + dim]).max()))
      i += dim
    eq["obs_checks"] += 1

  def warp_contacts():
    d_ = env.sim.data
    nac = int(npy(d_.nacon).reshape(-1)[0])
    return Counter(tuple(sorted(int(x) for x in p)) for p in npy(d_.contact.geom)[:nac].astype(int))

  def native_contacts(dn):
    return Counter(tuple(sorted((int(c.geom1), int(c.geom2)))) for c in dn.contact[:dn.ncon])

  def reset_to(f):
    start[0] = f
    env.reset()
    eq["reset_warmstart_max_abs_before_zeroing"] = max(eq["reset_warmstart_max_abs_before_zeroing"],
                                                       float(np.abs(npy(env.sim.data.qacc_warmstart[0])).max()))
    env.sim.data.qacc_warmstart[0] = tt(np.zeros(m.nv))
    o = venv.get_observations()
    if int(cmd.time_steps[0]) != f:
      raise RuntimeError(f"start frame not applied: {int(cmd.time_steps[0])} != {f}")
    return o

  def new_acc():
    return dict(sq=[], sv=[], dof=[], ceq=[], kf=[], k=[], worst=None, obs={}, pushes=0, ncon=[], nacon=[])

  def mj_step_rec(act):
    rec["on"] = True
    n0 = len(rec["f"])
    out = venv.step(act)
    rec["on"] = False
    eq["substeps_per_policy_step"].add(len(rec["f"]) - n0)
    return out, n0

  def compare_step(acc, k, pq, pv, pw, wset, a_np, q1, v1, n0):
    g.set_state(de, pq, pv, pw)
    same = native_contacts(de) == wset
    acc["ncon"].append(int(de.ncon))
    acc["nacon"].append(int(sum(wset.values())))
    de.ctrl[g.act] = g.targets(a_np)
    kfn = []
    for _ in range(g.decim):
      mujoco.mj_step(m, de)
      kfn.append(de.actuator_force[ka].copy())
    mujoco.mj_forward(m, de)
    kfw = np.array(rec["f"][n0:n0 + g.decim])[:, ka]
    eq["ctrl_max_abs"] = max(eq["ctrl_max_abs"], float(np.abs(de.ctrl - npy(env.sim.data.ctrl[0])).max()))
    dv = np.abs(de.qvel - v1)
    acc["sq"].append(float(np.abs(de.qpos - q1).max()))
    acc["sv"].append(float(dv.max()))
    acc["kf"].append(float(np.abs(np.array(kfn) - kfw).max()))
    acc["k"].append(k)
    acc["dof"].append(dof_name(int(np.argmax(dv))))
    acc["ceq"].append(bool(same))
    if acc["worst"] is None or acc["sv"][-1] > acc["worst"]["qvel_max_abs"]:
      acc["worst"] = dict(step=k, qvel_max_abs=acc["sv"][-1], qpos_max_abs=acc["sq"][-1], worst_dof=acc["dof"][-1],
                          contact_set_equal_at_pre_state=bool(same), ncon_at_pre_state=int(sum(wset.values())))

  def summarize_steps(acc):
    sv, dofs, ceq, ks = np.array(acc["sv"]), np.array(acc["dof"]), np.array(acc["ceq"]), np.array(acc["k"])
    big = sv > 0.1
    ph = labels["phase"]
    pn = [str(x) for x in labels["phase_names"]]
    by_phase = {}
    for p in sorted(set(ph[np.clip(ks, 0, len(ph) - 1)].tolist())):
      sel = ph[np.clip(ks, 0, len(ph) - 1)] == p
      by_phase[pn[p]] = dict(steps=int(sel.sum()), qvel_median=float(np.median(sv[sel])), qvel_max=float(sv[sel].max()),
                             frac_qvel_gt_0_1=float(np.mean(sv[sel] > 0.1)))
    return dict(steps=int(sv.size), pushes=acc["pushes"], qpos_max_abs=stat(acc["sq"]), qvel_max_abs=stat(sv),
                knee_force_per_substep_max_abs=stat(acc["kf"]),
                contact_set_equal_frac=float(ceq.mean()),
                contact_set_equal_frac_on_steps_qvel_gt_0_1=float(ceq[big].mean()) if big.any() else None,
                worst_dof_on_steps_qvel_gt_0_1=Counter(dofs[big].tolist()).most_common(6),
                by_reference_phase=by_phase, max_ncon_native=max(acc["ncon"]), max_nacon_warp=max(acc["nacon"]),
                worst_case=acc["worst"], obs_term_max_abs_at_perturbed_states=acc["obs"] or None)

  # ---- nominal rollout from frame 0 with every check
  f = 0
  nsteps = T - 1 - f
  obs = reset_to(f)
  q0, v0, _ = mj_state()
  nq0, nv0 = g.ref_state(mot, f)
  eq["init_qpos_max_abs"] = float(np.abs(q0 - nq0).max())
  eq["init_qvel_max_abs"] = float(np.abs(v0 - nv0).max())
  check_obs(f, eq["obs_term_max_abs"])
  nominal = new_acc()
  traj_m, snaps = [q0], []
  sub_f, sub_d, acts_m = [], [], []
  tw = time.perf_counter()
  for k in range(nsteps):
    pq, pv, pw = mj_state()
    wset = warp_contacts()
    with torch.no_grad():
      act = policy(obs)
    a_np = npy(act[0])
    acts_m.append(a_np)
    eq["action_impl_max_abs"] = max(eq["action_impl_max_abs"], float(np.abs(pol(npy(obs["actor"][0])) - a_np).max()))
    (obs, _, _, _), n0 = mj_step_rec(act)
    for j in range(n0, len(rec["f"])):
      sub_f.append(rec["f"][j][ka])
      sub_d.append(m.actuator_gainprm[ka, 0] * rec["ctrl"][j][ka] + m.actuator_biasprm[ka, 1] * rec["len"][j][ka] +
                   m.actuator_biasprm[ka, 2] * rec["vel"][j][ka])
    q1, v1, _ = mj_state()
    compare_step(nominal, k, pq, pv, pw, wset, a_np, q1, v1, n0)
    if k % 4 == 0 and len(snaps) < 48:
      snaps.append((pq, pv, pw, a_np))
    if int(cmd.time_steps[0]) != f + k + 1:
      eq["time_step_mismatch"] += 1
    check_obs(int(cmd.time_steps[0]), eq["obs_term_max_abs"])
    traj_m.append(q1)
  wall_m = time.perf_counter() - tw
  traj_m = np.array(traj_m)
  # mjlab re-run (run-to-run reproducibility of mujoco_warp)
  obs = reset_to(f)
  traj_r = [mj_state()[0]]
  for k in range(nsteps):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    traj_r.append(mj_state()[0])
  traj_r = np.array(traj_r)
  # native closed loop (flip_rollout, lag 0) + consistency with native_dance's plain stepping
  nat = flip_rollout(g, pol, mot, f, nsteps)
  traj_n = nat["traj"]
  print(f"[rollouts] mjlab {len(traj_m) - 1} steps ({wall_m:.1f}s incl. checks), native {len(traj_n) - 1} steps "
        f"({nat['wall']:.2f}s)", flush=True)

  # ---- off-nominal one-step equivalence (from frame 0): pushes every 20 steps / action noise N(0, 0.3)
  prng = np.random.default_rng(SEED + 100)
  perturbed = {}
  for scen in ("push", "noise"):
    acc = new_acc()
    obs = reset_to(f)
    for k in range(nsteps):
      if scen == "push" and k > 0 and k % 20 == 0:
        q = env.sim.data.qpos[0].clone()
        v = env.sim.data.qvel[0].clone()
        v[g.rv:g.rv + 3] += tt(prng.uniform([-0.5, -0.5, -0.2], [0.5, 0.5, 0.2]))
        v[g.rv + 3:g.rv + 6] += tt(prng.uniform(-0.5, 0.5, 3))
        q[torch.as_tensor(g.qadr)] += tt(prng.uniform(-0.15, 0.15, 29))
        v[torch.as_tensor(g.dadr)] += tt(prng.uniform(-1.0, 1.0, 29))
        env.sim.data.qpos[0] = q
        env.sim.data.qvel[0] = v
        env.sim.forward()
        env.sim.sense()
        env.obs_buf = env.observation_manager.compute(update_history=True)
        obs = venv.get_observations()
        check_obs(int(cmd.time_steps[0]), acc["obs"])
        acc["pushes"] += 1
      pq, pv, pw = mj_state()
      wset = warp_contacts()
      with torch.no_grad():
        act = policy(obs)
      if scen == "noise":
        act = act + torch.as_tensor(prng.normal(0.0, 0.3, tuple(act.shape)), dtype=act.dtype, device=act.device)
      a_np = npy(act[0])
      (obs, _, _, _), n0 = mj_step_rec(act)
      q1, v1, _ = mj_state()
      compare_step(acc, k, pq, pv, pw, wset, a_np, q1, v1, n0)
    perturbed[scen] = summarize_steps(acc)
    print(f"[perturbed:{scen}]", json.dumps(perturbed[scen])[:600], flush=True)

  # ---- single substep: 1 x mjwarp.step vs 1 x mj_step from identical state / ctrl / warm start
  sub_q, sub_v = [], []
  for pq, pv, pw, a_np in snaps:
    qw = pq.copy()
    qw[:3] += origin
    env.sim.data.qpos[0] = tt(qw)
    env.sim.data.qvel[0] = tt(pv)
    env.sim.data.qacc_warmstart[0] = tt(pw)
    ctrl = np.zeros(m.nu)
    ctrl[g.act] = g.targets(a_np)
    env.sim.data.ctrl[0] = tt(ctrl)
    orig = env.sim.step
    orig()
    q1, v1, _ = mj_state()
    g.set_state(de, pq, pv, pw)
    de.ctrl[:] = ctrl
    mujoco.mj_step(m, de)
    sub_q.append(float(np.abs(de.qpos - q1).max()))
    sub_v.append(float(np.abs(de.qvel - v1).max()))

  equivalence = dict(
    steps_checked=eq["obs_checks"], obs_term_max_abs=eq["obs_term_max_abs"],
    obs_all_terms_max_abs=max(eq["obs_term_max_abs"].values()),
    policy_impl_action_max_abs=eq["action_impl_max_abs"], ctrl_targets_max_abs=eq["ctrl_max_abs"],
    reset_state_npz_vs_mjlab=dict(qpos_max_abs=eq["init_qpos_max_abs"], qvel_max_abs=eq["init_qvel_max_abs"]),
    reset_warmstart_max_abs_before_zeroing=eq["reset_warmstart_max_abs_before_zeroing"],
    motion_time_step_mismatches=eq["time_step_mismatch"],
    substeps_recorded_per_policy_step=sorted(eq["substeps_per_policy_step"]),
    one_policy_step_4_substeps=summarize_steps(nominal), one_policy_step_4_substeps_perturbed=perturbed,
    one_substep=dict(qpos_max_abs=stat(sub_q), qvel_max_abs=stat(sub_v)))
  print("[equivalence]", json.dumps(equivalence)[:3000], flush=True)

  # ---- flip metrics for both sims (same code, recorded qpos) + divergence
  met_m, cur_m = flip_metrics(g, traj_m, dt, labels, np.array(sub_f), np.array(sub_d))
  met_n, cur_n = flip_metrics(g, traj_n, dt, labels, nat["knee_force"], nat["knee_demand"], nat["ncon"])
  met_r, _ = flip_metrics(g, traj_r, dt, labels)
  ref_info = {}
  try:  # what rl/eval_flip.py reported for this checkpoint (play cfg WITH its startup DR events, T-2 steps)
    jf = sorted(pdir.glob("flip_auto_model_*.json"))[0]
    ref_info = {k: json.loads(jf.read_text()).get(k) for k in ("robot_rotation_deg", "robot_peak_pelvis_m",
                                                              "robot_airborne_s", "landed_upright", "end_tilt_deg",
                                                              "end_pelvis_m")}
    ref_info["file"] = jf.name
  except Exception:  # noqa: BLE001
    pass
  div = event_divergence(g, traj_m, traj_n, labels, dt)
  div_r = event_divergence(g, traj_m, traj_r, labels, dt)
  print("[metrics] mjlab ", json.dumps(met_m), flush=True)
  print("[metrics] native", json.dumps(met_n), flush=True)
  print("[metrics] mjlab rerun", json.dumps(met_r), flush=True)
  print("[divergence] mjlab vs native", json.dumps({k: v for k, v in div.items() if k != "curve_every_5_steps"}), flush=True)
  print("[divergence] mjlab vs rerun ", json.dumps({k: v for k, v in div_r.items() if k != "curve_every_5_steps"}), flush=True)
  video = None
  if not a.no_video:
    video = render_side_by_side(g, mot, 0, traj_m, traj_n, ("mjlab (mujoco_warp, GPU)", "native MuJoCo (CPU)"),
                                VID_DIR / f"backflip_{short(a.policy)}_side_by_side.mp4")
  res = dict(policy=a.policy, policy_file=str(pdir / "policy.pt"), motion=mot.path, motion_fps=mot.fps, frames=T,
             step_dt=dt, decimation=g.decim, mujoco_native=mujoco.__version__, device_mjlab=E["dev"],
             knee_limit=KNEE_LIMIT, randomisation=dict(removed_events=E["removed_events"],
                                                       removed_terminations=E["removed_terms"],
                                                       rsi_ranges="all zero", obs_corruption="off (play cfg)"),
             success_rule=SUCCESS_RULE, model_check=mcheck, equivalence=equivalence,
             metrics=dict(mjlab=met_m, native=met_n, mjlab_rerun=met_r), eval_flip_json=ref_info,
             divergence=div, divergence_mjlab_rerun=div_r, native_wall_s=round(nat["wall"], 3),
             native_realtime_factor=round(nsteps * dt / nat["wall"], 1), video=video)
  (HERE / f"results_flip_{a.policy}.json").write_text(json.dumps(res, indent=1, ensure_ascii=False))
  np.savez_compressed(HERE / f"traj_flip_{a.policy}.npz", mjlab=traj_m, native=traj_n, mjlab_rerun=traj_r,
                      actions_mjlab=np.array(acts_m), actions_native=nat["actions"],
                      knee_force_mjlab=np.array(sub_f), knee_force_native=nat["knee_force"],
                      **{f"curve_{s}_{k}": v for s, c in (("mjlab", cur_m), ("native", cur_n)) for k, v in c.items()})
  print("[done]", a.policy, flush=True)


# ---------------------------------------------------------------------------------------------- mjlab delay check
def mjlab_delay_mode(a):
  pdir, info, g, pol, mot, labels, dt = load_ctx(a)
  L = int(a.lag)
  E = build_mjlab(pdir, lag=L)
  env, venv, policy, cmd, start, npy, rec = E["env"], E["venv"], E["policy"], E["cmd"], E["start"], E["npy"], E["rec"]
  origin, T = E["origin"], mot.T
  start[0] = 0
  env.reset()
  env.sim.data.qacc_warmstart[0] = torch.zeros_like(env.sim.data.qacc_warmstart[0])
  obs = venv.get_observations()
  q = npy(env.sim.data.qpos[0]).copy()
  q[:3] -= origin
  traj, acts, ctrls = [q], [], []
  for k in range(T - 1):
    with torch.no_grad():
      act = policy(obs)
    acts.append(npy(act[0]))
    rec["on"] = True
    n0 = len(rec["ctrl"])
    obs, _, _, _ = venv.step(act)
    rec["on"] = False
    ctrls += rec["ctrl"][n0:]
    q = npy(env.sim.data.qpos[0]).copy()
    q[:3] -= origin
    traj.append(q)
  traj, ctrls = np.array(traj), np.array(ctrls)
  # expected ctrl from mjlab's own actions through the native delay buffer (same code as flip_rollout)
  hist, exp = deque(maxlen=L + 1), []
  for a_np in acts:
    for _ in range(g.decim):
      hist.append(g.targets(a_np))
      exp.append(hist[0])
  exp = np.array(exp)
  ctrl_diff = float(np.abs(ctrls[:, g.act] - exp).max())
  per_sub = np.abs(ctrls[:, g.act] - exp).max(1)
  bad = np.where(per_sub > 1e-5)[0]
  # which delay model does mjlab actually implement? lags L-1..L+1, history backfilled with the first target or
  # with the default pose (action 0)
  variants = {}
  for LL in range(max(L - 2, 0), L + 3):
    for fill in ("first", "default", "zeros"):
      h = deque([g.targets(np.zeros(29)) if fill == "default" else np.zeros(29)] * LL, maxlen=LL + 1) \
          if fill != "first" else deque(maxlen=LL + 1)
      e2 = []
      for a_np in acts:
        for _ in range(g.decim):
          h.append(g.targets(a_np))
          e2.append(h[0])
      variants[f"lag{LL}_{fill}"] = float(np.abs(ctrls[:, g.act] - np.array(e2)).max())
  print("[delay-diag] substeps differing:", bad[:20].tolist(), len(bad), "variants:", json.dumps(variants), flush=True)
  # mjlab's obs 'actions' term = undelayed policy output?  (compare last obs actions with last policy action)
  last_obs_act = npy(obs["actor"][0])[-29:]
  best_fill = min(("first", "default", "zeros"), key=lambda fl: variants[f"lag{L}_{fl}"])
  nat = flip_rollout(g, pol, mot, 0, T - 1, lag=L, fill=best_fill)
  nat_first = flip_rollout(g, pol, mot, 0, T - 1, lag=L, fill="first")
  met_nf, _ = flip_metrics(g, nat_first["traj"], dt, labels, nat_first["knee_force"], nat_first["knee_demand"])
  met_m, _ = flip_metrics(g, traj, dt, labels)
  met_n, _ = flip_metrics(g, nat["traj"], dt, labels, nat["knee_force"], nat["knee_demand"], nat["ncon"])
  div = event_divergence(g, traj, nat["traj"], labels, dt)
  res = dict(policy=a.policy, lag_physics_steps=L, delay_ms=L * 5, substeps=len(ctrls),
             ctrl_vs_native_delay_buffer_max_abs=ctrl_diff, substeps_differing=bad.tolist(),
             ctrl_diff_by_delay_model=variants,
             obs_last_action_vs_policy_output_max_abs=float(np.abs(last_obs_act - acts[-1]).max()),
             mjlab_fill_after_reset=best_fill, ctrl_diff_with_that_fill=variants[f"lag{L}_{best_fill}"],
             metrics=dict(mjlab=met_m, native=met_n, native_fill_first=met_nf), divergence=div)
  print("[delay]", json.dumps({k: v for k, v in res.items() if k != "divergence"}), flush=True)
  (HERE / f"results_flip_{a.policy}_delay{L}.json").write_text(json.dumps(res, indent=1))


# --------------------------------------------------------------------------------------------------- native modes
def model_from_args(a):
  if a.xml:
    xml = Path(a.xml) if Path(a.xml).is_absolute() else HERE / a.xml
    return load_xml_model(xml, a.assets), str(xml)
  return mujoco.MjModel.from_binary_path(str(HERE / "models" / "flip.mjb")), "models/flip.mjb"


def model_vs_mjb(m):
  ref = dict(np.load(HERE / "models" / "flip_fields.npz"))
  return {f_: (float(np.abs(np.asarray(getattr(m, f_), float) - v).max())
               if np.asarray(getattr(m, f_)).shape == v.shape else "shape") for f_, v in ref.items()}


def native_mode(a):
  m, src = model_from_args(a)
  pdir, info, g, pol, mot, labels, dt = load_ctx(a, m)
  out = dict(policy=a.policy, mujoco=mujoco.__version__, model=src, model_check_vs_mjb=model_vs_mjb(m),
             knee_forcerange=g.knee_limit())
  print(f"[{a.tag}] mujoco {mujoco.__version__} model {src}: max field diff vs flip.mjb "
        f"{max(v for v in out['model_check_vs_mjb'].values() if isinstance(v, float)):.2e}, knees {g.knee_limit()}",
        flush=True)
  ref = np.load(HERE / f"traj_flip_{a.policy}.npz")
  nat = flip_rollout(g, pol, mot, 0, mot.T - 1)
  out["metrics"], _ = flip_metrics(g, nat["traj"], dt, labels, nat["knee_force"], nat["knee_demand"], nat["ncon"])
  out["divergence_vs_native_mjb"] = event_divergence(g, ref["native"], nat["traj"], labels, dt)
  out["divergence_vs_mjlab"] = event_divergence(g, ref["mjlab"], nat["traj"], labels, dt)
  out["wall_s"] = round(nat["wall"], 3)
  # warp-like clamp emulation (see flip_rollout): does it remove the mjlab-vs-native divergence?
  wc = flip_rollout(g, pol, mot, 0, mot.T - 1, warp_clamp=True)
  out["metrics_warp_clamp"], _ = flip_metrics(g, wc["traj"], dt, labels, wc["knee_force"], wc["knee_demand"], wc["ncon"])
  out["divergence_warp_clamp_vs_mjlab"] = event_divergence(g, ref["mjlab"], wc["traj"], labels, dt)
  print(f"[{a.tag}] warp-clamp emulation", json.dumps(out["metrics_warp_clamp"]), flush=True)
  for lab, key in (("native", "divergence_vs_mjlab"), ("native warp-clamp", "divergence_warp_clamp_vs_mjlab")):
    print(f"[{a.tag}] mjlab vs {lab}:", json.dumps({k: (v["pelvis_pos_diff_m"], v["torso_ori_diff_deg"],
                                                        v["joint_max_abs_upto_rad"]) for k, v in out[key].items()
                                                    if isinstance(v, dict)}), flush=True)
  print(f"[{a.tag}]", json.dumps(out["metrics"]), flush=True)
  print(f"[{a.tag}] vs native mjb:", json.dumps({k: v for k, v in out["divergence_vs_native_mjb"].items()
                                                 if k != "curve_every_5_steps"}), flush=True)
  (HERE / f"results_flip_{a.policy}_{a.tag}.json").write_text(json.dumps(out, indent=1))


def scenarios_mode(a):
  m, src = model_from_args(a)
  pdir, info, g, pol, mot, labels, dt = load_ctx(a, m)
  T = mot.T
  sel = [s for s in SCENARIOS if not a.scenarios or s[0] in a.scenarios.split(",")]
  out = dict(policy=a.policy, mujoco=mujoco.__version__, model=src, runs_per_scenario=a.runs, success_rule=SUCCESS_RULE,
             warp_clamp_emulation=bool(a.warp_clamp),
             start_jitter=dict(root_xy_m=a.jit_xy, roll_pitch_rad=a.jit_rp, yaw_rad=a.jit_yaw, joint_pos_rad=a.jit_q),
             push_range_lo=PUSH_LO.tolist(), push_range_hi=PUSH_HI.tolist(), scenarios=[])
  t0 = time.perf_counter()
  for name, desc, kw in sel:
    g.set_variant(friction=kw.get("friction"), kp_scale=kw.get("kp_scale"))
    rows, exact = [], None
    for i in range(a.runs + 1):  # run 0 = exact reference start (no jitter, no randomness unless push)
      rng = np.random.default_rng([SEED, i])  # common random numbers across scenarios
      init = None if i == 0 else jitter_state(g, *g.ref_state(mot, 0), rng, a)
      pushes = None
      if kw.get("push"):
        prng = np.random.default_rng([SEED, 7, i])
        k = int(prng.integers(10, 61)) if kw["push"] == "pre" else int(prng.integers(156, 163))
        pushes = {k: prng.uniform(PUSH_LO, PUSH_HI)}
      r = flip_rollout(g, pol, mot, 0, T - 1, lag=kw.get("lag", 0), pushes=pushes, init=init, warp_clamp=a.warp_clamp)
      met, _ = flip_metrics(g, r["traj"], dt, labels, r["knee_force"], r["knee_demand"], r["ncon"])
      if i == 0:
        exact = met
      else:
        rows.append(met)
    g.set_variant()
    arr = lambda k: np.array([r[k] for r in rows], float)
    pct = lambda x: [round(float(v), 2) for v in np.percentile(x, [5, 50, 95])]
    s = dict(name=name, description=desc, runs=len(rows), success_rate=round(float(arr("success").mean()), 3),
             falls=int(arr("fell").sum()), early_falls=int(arr("early_fall").sum()),
             rotation_deg_p5_50_95=pct(arr("rotation_deg")), peak_pelvis_m_p5_50_95=pct(arr("peak_pelvis_m")),
             airborne_s_p5_50_95=pct(arr("airborne_s")), airborne_no_contact_s_p5_50_95=pct(arr("airborne_no_contact_s")),
             tail_tilt_max_deg_p5_50_95=pct(arr("tail_tilt_max_deg")),
             tail_pelvis_min_m_p5_50_95=pct(arr("tail_pelvis_min_m")),
             knee_torque_max_Nm=round(float(arr("knee_torque_max_Nm").max()), 2),
             knee_at_limit_frac_mean=round(float(arr("knee_at_limit_frac").mean()), 4),
             knee_limit_respected_all=bool(all(r["knee_torque_respects_limit"] for r in rows)),
             exact_start=exact)
    out["scenarios"].append(s)
    print(f"[{a.tag}] {name:9s} success {s['success_rate']:.2f} ({len(rows)} runs) falls {s['falls']} rot p5/50/95 "
          f"{s['rotation_deg_p5_50_95']} tail tilt {s['tail_tilt_max_deg_p5_50_95']} | exact start: success "
          f"{exact['success']} rot {exact['rotation_deg']} | knee max {s['knee_torque_max_Nm']} N.m "
          f"at-limit {s['knee_at_limit_frac_mean']:.3f}", flush=True)
  out["wall_s"] = round(time.perf_counter() - t0, 1)
  (HERE / f"results_flip_{a.policy}_scen_{a.tag}.json").write_text(json.dumps(out, indent=1))


# --------------------------------------------------------------------------------------------------- report mode
def report_mode(a):
  pols = [p.stem.replace("results_flip_", "") for p in sorted(HERE.glob("results_flip_backflip_*.json"))
          if re.fullmatch(r"results_flip_backflip_r\d+_[a-z0-9]+", p.stem)][::-1]  # newest round first
  allres = {}
  L = ["# Backflip sim2sim: mjlab (mujoco_warp) vs native MuJoCo", "",
       "Generated by `sim2sim/native_flip.py --mode report`. All numbers are measured by the scripts in sim2sim/ "
       "(export_flip_model.py, native_flip.py); nothing is estimated.", "",
       f"Success rule (same code for every sim / run): {SUCCESS_RULE}. Rotation = rl/eval_flip.cum_pitch on the torso "
       "quaternion; airborne = longest run with every robot body origin > 5 cm and pelvis > 0.45 m (eval_flip "
       "definition); 'no-contact' airborne = longest run without any robot-floor contact; landing = first contact "
       "after that run; fell = pelvis < 0.4 m in the last 0.5 s.", ""]
  exp_log = HERE / "logs" / "export_flip.log"
  if exp_log.exists():
    lines = exp_log.read_text(errors="ignore").splitlines()
    keep = [x for x in lines if x.startswith("[verify] max over") or x.startswith("[verify] KNEE") or
            x.startswith("[verify] hip roll") or x.startswith("[verify] non-actuator") or
            x.startswith("[verify] actuators that differ")]
    L += ["## Exported model (models/flip.mjb, flip.xml)", "", "From logs/export_flip.log:", ""] + \
         [f"- `{x[:400]}`" for x in keep] + [""]
  for P in pols:
    r = json.loads((HERE / f"results_flip_{P}.json").read_text())
    allres[P] = r
    e, mc = r["equivalence"], r["model_check"]
    L += [f"## {P} ({r['frames']} frames @ {r['motion_fps']} fps, knee limit {r['knee_limit']} N.m)", "",
          f"Randomisation off: removed events {r['randomisation']['removed_events']}, removed terminations "
          f"{r['randomisation']['removed_terminations']}; RSI ranges zero; obs corruption off.", "",
          "### Model", "",
          f"- exported flip.mjb vs runtime mj_model: max abs over {len(mc['exported_vs_runtime_mj_model_max_abs'])} "
          f"fields = {max(mc['exported_vs_runtime_mj_model_max_abs'].values()):.1e}; warp model vs nominal: "
          f"{max(v for v in mc['warp_model_vs_nominal_max_abs'].values() if isinstance(v, float)):.1e}",
          f"- knee actuators {mc['knee_actuators']}: forcerange in flip.mjb {mc['mjb_knee_forcerange']}, in the warp "
          f"(GPU) model {mc.get('warp_knee_forcerange')}", ""]
    L += [f"### Equivalence (state copied mjlab -> native at every step of the frame-0 rollout, {e['steps_checked']} "
          "obs checks)", "", "| obs term | max abs diff |", "|---|---|"]
    L += [f"| {k} | {v:.2e} |" for k, v in e["obs_term_max_abs"].items()]
    L += ["", f"- policy re-implementation (same obs): max |action diff| {e['policy_impl_action_max_abs']:.2e}; ctrl "
          f"targets {e['ctrl_targets_max_abs']:.2e}; reset state npz rebuild vs mjlab qpos "
          f"{e['reset_state_npz_vs_mjlab']['qpos_max_abs']:.2e} / qvel {e['reset_state_npz_vs_mjlab']['qvel_max_abs']:.2e}; "
          f"motion time-step mismatches {e['motion_time_step_mismatches']}; substeps per policy step "
          f"{e['substeps_recorded_per_policy_step']}", "",
          "One policy step (4 substeps) from the identical pre-step state, action and qacc_warmstart (max over DOFs of "
          "|native - mjlab|; knee force = max over the 4 substeps and both knees of |actuator_force native - warp|):", "",
          "| scenario | steps | qvel median | qvel p99 | qvel max | frac qvel>0.1 | frac qvel>1 | qpos max | knee force "
          "median / max (N.m) | contact set equal | equal on qvel>0.1 steps | max ncon native / warp | largest-diff DOF "
          "(qvel>0.1 steps) |", "|---|---|---|---|---|---|---|---|---|---|---|---|---|"]
    rows = [("nominal (frame 0)", e["one_policy_step_4_substeps"])] + \
           [(f"{k} ({v['pushes']} pushes)" if v["pushes"] else k, v)
            for k, v in e["one_policy_step_4_substeps_perturbed"].items()]
    for lab, s in rows:
      qv, qp, kf = s["qvel_max_abs"], s["qpos_max_abs"], s["knee_force_per_substep_max_abs"]
      ce = s["contact_set_equal_frac_on_steps_qvel_gt_0_1"]
      dofs = ", ".join(f"{n} {c}" for n, c in s["worst_dof_on_steps_qvel_gt_0_1"]) or "-"
      L.append(f"| {lab} | {s['steps']} | {qv['median']:.1e} | {qv['p99']:.1e} | {qv['max']:.2f} | "
               f"{qv['frac_gt_1e_1']:.2%} | {qv['frac_gt_1']:.2%} | {qp['max']:.1e} | {kf['median']:.1e} / {kf['max']:.2f} | "
               f"{s['contact_set_equal_frac']:.1%} | {'-' if ce is None else f'{ce:.1%}'} | "
               f"{s['max_ncon_native']} / {s['max_nacon_warp']} | {dofs} |")
    bp = e["one_policy_step_4_substeps"]["by_reference_phase"]
    L += ["", "Nominal one-step qvel difference by reference phase: " +
          "; ".join(f"{k}: {v['steps']} steps, median {v['qvel_median']:.1e}, max {v['qvel_max']:.2f}, "
                    f"frac>0.1 {v['frac_qvel_gt_0_1']:.1%}" for k, v in bp.items())]
    s1 = e["one_substep"]
    L += [f"- single substep ({s1['qvel_max_abs']['n']} states along the rollout): qpos median "
          f"{s1['qpos_max_abs']['median']:.1e} / max {s1['qpos_max_abs']['max']:.1e}; qvel median "
          f"{s1['qvel_max_abs']['median']:.1e} / max {s1['qvel_max_abs']['max']:.1e}", ""]
    # closed loop
    M = r["metrics"]
    cross = {q.stem.split(f"{P}_", 1)[1]: json.loads(q.read_text()) for q in sorted(HERE.glob(f"results_flip_{P}_*.json"))
             if not any(s in q.stem for s in ("_scen_", "_delay", "diag"))}
    cols = [("success", "success"), ("rotation_deg", "rotation (deg)"), ("peak_pelvis_m", "peak pelvis (m)"),
            ("airborne_s", "airborne (s)"), ("airborne_no_contact_s", "no-contact airborne (s)"),
            ("takeoff_offset_steps", "take-off offset (steps)"), ("landing_offset_steps", "landing offset (steps)"),
            ("landing_tilt_deg", "landing tilt (deg)"), ("landing_tilt_max_0p5s_deg", "max tilt 0.5 s after landing"),
            ("end_tilt_deg", "end tilt (deg)"), ("tail_tilt_max_deg", "max tilt last 0.5 s"),
            ("tail_pelvis_min_m", "min pelvis last 0.5 s (m)"), ("fell", "fell"),
            ("knee_torque_max_Nm", "max knee torque (N.m)"), ("knee_at_limit_frac", "frac substeps knee at limit"),
            ("knee_pd_demand_max_Nm", "max unclipped knee PD demand (N.m)")]
    sims = [("mjlab", M["mjlab"]), ("mjlab re-run", M["mjlab_rerun"]), ("native 3.5 (.mjb)", M["native"])] + \
           [(f"native {t} (MuJoCo {c['mujoco']}, xml)", c["metrics"]) for t, c in cross.items()] + \
           [(f"native {t} + warp-clamp emulation", c["metrics_warp_clamp"]) for t, c in cross.items()
            if "metrics_warp_clamp" in c]
    L += ["### Closed loop from frame 0 (same initial state)", "",
          "| metric | " + " | ".join(s for s, _ in sims) + " |", "|---|" + "---|" * len(sims)]
    for k, lab in cols:
      L.append(f"| {lab} | " + " | ".join("-" if x.get(k) is None else str(x.get(k)) for _, x in sims) + " |")
    L += ["", "Take-off / landing offsets are relative to the reference (flight frames from labels_50fps.npz); "
          "mjlab knee torques are per physics substep (sim.step wrapped), native ones per mj_step; the re-run column "
          "has no torque record."]
    if r.get("eval_flip_json"):
      L += [f"- for comparison, rl/eval_flip.py on this checkpoint ({r['eval_flip_json'].get('file')}, play cfg WITH "
            f"its startup DR events, terminations off): {json.dumps({k: v for k, v in r['eval_flip_json'].items() if k != 'file'})}"]
    L += ["", "Divergence along the frame-0 closed loop (event steps from the reference labels; state k pairs with "
          "frame k-1):", "",
          "| pair | event | step | pelvis pos diff (m) | torso ori diff (deg) | rotation diff (deg) | joint max abs at "
          "(rad) | joint RMS at (rad) | joint max abs up to (rad) |", "|---|---|---|---|---|---|---|---|---|"]
    pairs = [("mjlab vs native 3.5", r["divergence"]), ("mjlab vs mjlab re-run", r["divergence_mjlab_rerun"])]
    for t, c in cross.items():
      pairs += [(f"native 3.5 vs native {t}", c["divergence_vs_native_mjb"])]
      if "divergence_warp_clamp_vs_mjlab" in c:
        pairs += [(f"mjlab vs native {t} + warp-clamp emulation", c["divergence_warp_clamp_vs_mjlab"])]
    for lab, dv in pairs:
      for ev in ("takeoff", "mid_flight", "landing", "end"):
        x = dv[ev]
        L.append(f"| {lab} | {ev} | {x['step']} | {x['pelvis_pos_diff_m']:.4f} | {x['torso_ori_diff_deg']:.2f} | "
                 f"{x['rotation_diff_deg']:.2f} | {x['joint_max_abs_at_rad']:.4f} | {x['joint_rms_at_rad']:.4f} | "
                 f"{x['joint_max_abs_upto_rad']:.4f} |")
    L += ["", "First step at which the trajectories differ at all: " +
          ", ".join(f"{lab}: {dv['first_differing_step']}" for lab, dv in pairs)]
    L += [f"- native closed loop speed: {r['native_realtime_factor']}x real time (single thread)"]
    for t, c in cross.items():
      mx = max(v for v in c["model_check_vs_mjb"].values() if isinstance(v, float))
      L += [f"- cross check {t}: MuJoCo {c['mujoco']}, {c['model']}: model fields vs flip.mjb max abs {mx:.1e}; knee "
            f"forcerange {c['knee_forcerange']}"]
    # latency check
    for q in sorted(HERE.glob(f"results_flip_{P}_delay*.json")):
      dl = json.loads(q.read_text())
      mm, nn, nf = dl["metrics"]["mjlab"], dl["metrics"]["native"], dl["metrics"]["native_fill_first"]
      first_diff = dl["ctrl_diff_by_delay_model"][f"lag{dl['lag_physics_steps']}_first"]
      L += [f"- latency implementation check, lag {dl['lag_physics_steps']} physics steps ({dl['delay_ms']} ms): mjlab "
            f"DelayedActuatorCfg(min=max lag, hold 0) per-substep ctrl vs the native delay buffer fed with mjlab's "
            f"actions: the lag is exactly {dl['lag_physics_steps']} physics steps; after the reset mjlab sends ctrl = 0 "
            f"rad for the first {dl['lag_physics_steps']} substeps (best-matching fill '{dl['mjlab_fill_after_reset']}', "
            f"max abs ctrl diff {dl['ctrl_diff_with_that_fill']:.1e} over {dl['substeps']} substeps; with the first "
            f"target as fill: {first_diff:.2f} on substeps "
            f"{dl['substeps_differing']}); obs last-action = undelayed policy output (max abs "
            f"{dl['obs_last_action_vs_policy_output_max_abs']:.1e}). Closed loop with this delay (same fill): mjlab "
            f"success {mm['success']} (rot {mm['rotation_deg']}, max tilt last 0.5 s {mm['tail_tilt_max_deg']}, fell "
            f"{mm['fell']}), native success {nn['success']} (rot {nn['rotation_deg']}, tilt {nn['tail_tilt_max_deg']}, "
            f"fell {nn['fell']}); native with first-target fill (used in the scenario suite): success {nf['success']} "
            f"(rot {nf['rotation_deg']}, tilt {nf['tail_tilt_max_deg']})"]
    # where the one-step difference comes from
    td = HERE / f"results_flip_{P}_takeoffdiag.json"
    if td.exists():
      x = json.loads(td.read_text())
      L += ["", "### Where mjlab and native disagree (diag_flip_takeoff.py)", "",
            "One physics substep from the identical state / ctrl / warm start at every policy step of an mjlab frame-0 "
            "rollout. Forward-pass quantities of that step (max abs diff over DOFs) vs the next qvel; 'hand' = "
            "implicitfast velocity update recomputed by hand from the native forward pass, v+ = v + h (M - h D)^-1 "
            "M qacc with D = -dof_damping - kd, either with every actuator's kd ('all') or without the actuators whose "
            "PD force is clamped by forcerange ('unclamped').", "",
            "| phase | steps | steps with a clamped actuator | qfrc_actuator | qacc_smooth | qfrc_constraint | qacc | next qvel "
            "max | hand 'unclamped' vs native | hand 'all' vs native | hand 'all' vs warp | hand 'unclamped' vs warp |",
            "|---|---|---|---|---|---|---|---|---|---|---|---|"]
      for ph_, b in x["by_phase"].items():
        L.append(f"| {ph_} | {b['steps']} | {b['steps_with_clamped_actuator']} | {b['qfrc_actuator_max']:.1e} | "
                 f"{b['qacc_smooth_max']:.1e} | {b['qfrc_constraint_max']:.1e} | {b['qacc_max']:.1e} | "
                 f"{b['qvel_next_max']:.2e} | {b['hand_unclamped_vs_native_max']:.1e} | {b['hand_all_vs_native_max']:.1e} | "
                 f"{b['hand_all_vs_warp_max']:.1e} | {b['hand_unclamped_vs_warp_max']:.1e} |")
      c_ = x["steps_qvel_next_gt_0_05"]
      L += ["", f"- steps with next-qvel diff > 0.05 rad/s: {c_['n']} of {c_['total_steps']}, all {c_['with_clamped_actuator']} "
            f"of them with at least one force-clamped actuator; {c_['steps_without_large_diff_with_clamped']} steps had a "
            "clamped actuator without a large diff."]
    sd = HERE / f"results_flip_{P}_solverdiag.json"
    if sd.exists():
      x = json.loads(sd.read_text())
      L += ["- native solver convergence / float32 sensitivity along the native frame-0 loop (diag_flip_solver.py; next "
            "qvel max abs diff vs the nominal step): " + "; ".join(
              f"{k}: iterations 100 & tol 1e-12 {b['iters100_qvel_diff_max']:.0e}, float32-rounded state "
              f"{b['f32_state_qvel_diff_max']:.0e}, float32 ctrl {b['f32_ctrl_qvel_diff_max']:.0e}, substeps at the "
              f"10-iteration cap {b['substeps_at_iteration_cap_frac']:.1%}" for k, b in x["by_phase"].items())]
    # scenarios
    order = {"mj350": 0, "mj316": 1, "mj350wc": 2}
    for q in sorted(HERE.glob(f"results_flip_{P}_scen_*.json"), key=lambda p: order.get(p.stem.split("_scen_")[1], 9)):
      sc = json.loads(q.read_text())
      tag = q.stem.split("_scen_", 1)[1]
      wcl = (" WITH the mujoco_warp clamped-actuator damping emulated (= mjlab dynamics)"
             if sc.get("warp_clamp_emulation") else " (plain MuJoCo C dynamics)")
      L += ["", f"### Native perturbation scenarios ({tag}: MuJoCo {sc['mujoco']}, {Path(sc['model']).name}{wcl}; "
            f"{sc['runs_per_scenario']} runs each + 1 exact-start run)", "",
            f"Each run starts from the reference frame-0 state with a small random start jitter "
            f"{json.dumps(sc['start_jitter'])} (uniform, seeded; the same seeds in every scenario). Pushes add a "
            f"uniform root velocity in [{sc['push_range_lo']}, {sc['push_range_hi']}] (world lin m/s xyz, ang rad/s "
            "xyz; half the training push_robot ranges) once per run. Latency = fixed delay of the position targets in "
            "physics steps (5 ms each), DelayBuffer semantics; the policy's last-action observation is its undelayed "
            "output.", "",
            "| scenario | description | success rate | falls | rotation p5/50/95 (deg) | max tilt last 0.5 s p5/50/95 | "
            "min pelvis last 0.5 s p5/50/95 | no-contact airborne p5/50/95 (s) | max knee torque (N.m) | mean frac "
            "substeps knee at limit | exact start: success / rot / tilt |", "|---|---|---|---|---|---|---|---|---|---|---|"]
      for s in sc["scenarios"]:
        ex = s["exact_start"]
        L.append(f"| {s['name']} | {s['description']} | {s['success_rate']:.0%} ({int(round(s['success_rate'] * s['runs']))}"
                 f"/{s['runs']}) | {s['falls']} | {s['rotation_deg_p5_50_95']} | {s['tail_tilt_max_deg_p5_50_95']} | "
                 f"{s['tail_pelvis_min_m_p5_50_95']} | {s['airborne_no_contact_s_p5_50_95']} | {s['knee_torque_max_Nm']} | "
                 f"{s['knee_at_limit_frac_mean']:.3f} | {ex['success']} / {ex['rotation_deg']} / {ex['tail_tilt_max_deg']} |")
    if r.get("video"):
      L += ["", f"Video: `{r['video']}` (left = recorded mjlab qpos, right = native rollout, same native renderer; green "
                "ghost = reference frame k-1 re-anchored to the robot's torso xy + yaw)"]
    L.append("")
  L += ["## Notes / assumptions", "",
        "- Native side uses no mjlab code (observation, reference lookup, JointPositionAction, reset state, rsl_rl actor "
        "re-implemented in native_dance.py, imported unchanged); flip metrics use rl/eval_flip.cum_pitch (imported).",
        "- Rollouts run from frame 0 for T-1 = 189 policy steps (the last frame mjlab serves before it re-samples); no "
        "terminations, so a failed flip is played to the end and judged by the success rule.",
        "- Knee torque: native = actuator_force of both knee actuators after every mj_step; mjlab = the same field read "
        "after every mujoco_warp substep (env.sim.step wrapped). 'unclipped demand' = kp (ctrl - q) - kd qd at the "
        "pre-step state; the applied force is clamped to the forcerange (+-120 N.m for the knees) in both sims.",
        "- Scenario runs: start jitter, push and seed per run index are identical across scenarios (paired comparison). "
        "The jitter is part of every scenario incl. 'nominal'; the exact-start run is listed separately.",
        "- Latency in the scenario suite: fixed lag in physics steps (4 = 20 ms, 8 = 40 ms), history filled with the first "
        "policy target; mjlab's DelayedActuator instead outputs ctrl 0 rad for the first `lag` substeps after a reset "
        "(measured above), which matters only right after the reset.",
        "- Clamped-actuator damping: in MuJoCo C 3.5 (implicitfast; hand check in the diag table) an actuator whose force "
        "is clamped by forcerange contributes no -kd term to the implicit velocity derivative; mujoco_warp keeps -kd for "
        "every actuator (MuJoCo 3.16 was not hand-checked, but its closed loops and warp-clamp emulation runs equal the "
        "3.5 ones in the tables). This was not checked for the dance policies. The forward pass (actuator / bias / constraint forces, qacc) agrees; the next velocity differs on steps "
        "with a clamped actuator (ankle / waist / hip pitch / wrist pitch at take-off and in flight). 'warp-clamp "
        "emulation' reproduces mujoco_warp in native MuJoCo by switching forcelimited off and choosing ctrl so that the PD "
        "force at the pre-step state equals the clamped force.",
        ""]
  (HERE / "results_flip.json").write_text(json.dumps(allres, indent=1, ensure_ascii=False))
  (HERE / "results_flip.md").write_text("\n".join(L), encoding="utf-8")
  print("\n".join(L))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--mode", choices=("mjlab", "mjlab_delay", "native", "scenarios", "report"), required=True)
  ap.add_argument("--policy", default="backflip_r14_fid2")
  ap.add_argument("--xml", default=None, help="native/scenarios: scene XML instead of flip.mjb (other MuJoCo versions)")
  ap.add_argument("--assets", default=str(G1_ASSETS))
  ap.add_argument("--tag", default="mj350")
  ap.add_argument("--lag", type=int, default=4)
  ap.add_argument("--runs", type=int, default=100)
  ap.add_argument("--scenarios", default=None)
  ap.add_argument("--jit_xy", type=float, default=0.02)
  ap.add_argument("--jit_rp", type=float, default=0.02)
  ap.add_argument("--jit_yaw", type=float, default=0.05)
  ap.add_argument("--jit_q", type=float, default=0.02)
  ap.add_argument("--no_video", action="store_true")
  ap.add_argument("--warp_clamp", action="store_true", help="scenarios: emulate mujoco_warp's clamped-actuator damping")
  a = ap.parse_args()
  torch.set_num_threads(1)
  {"mjlab": mjlab_mode, "mjlab_delay": mjlab_delay_mode, "native": native_mode, "scenarios": scenarios_mode,
   "report": report_mode}[a.mode](a)
