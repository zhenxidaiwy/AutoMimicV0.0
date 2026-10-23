"""Adversarial, independent check of the get-up sim2sim (native_getup.py). Writes only to sim2sim/verify_getup_out/.

The native side here is re-implemented from scratch (no code from native_getup.py except the balanced 4-pose reset
wrapper for the closed loop): obs from mj_objectVelocity (not the sensors), gravity from qpos quaternion, joint order /
default pose / action scale+offset read from the RUNNING mjlab env (not from models/getup_info.json), numpy float64
actor written from the checkpoint tensors.

  python verify_getup_check.py check   [--n 32 --seed 123]   per-term obs / action / ctrl / physics diffs on new states
  python verify_getup_check.py closed  [--n 16 --seed 1]     closed loop mjlab vs my native, metrics recomputed
  python verify_getup_check.py replay                         my native from THEIR seed-0 initial states vs their logs
"""
import argparse
import json
import os
import sys
import time
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
VOUT = HERE / "verify_getup_out"
POLICY = ROOT / "policies" / "getup_auto_r08" / "policy.pt"
KNOBS = ROOT / "policies" / "getup_auto_r08" / "knobs.json"
TASK = "Dance-Recovery-G1-auto"
MJB = HERE / "models" / "getup.mjb"
DEV = "cuda:0"


# ------------------------------------------------------------------ independent native implementation
class NpActor:
  def __init__(self, path=POLICY, eps=1e-2):
    import torch
    sd = torch.load(path, map_location="cpu", weights_only=False)["actor_state_dict"]
    self.keys = {k: list(v.shape) for k, v in sd.items()}
    self.mean = sd["obs_normalizer._mean"].double().numpy().reshape(-1)
    self.std = sd["obs_normalizer._std"].double().numpy().reshape(-1)
    idx = sorted({int(k.split(".")[1]) for k in sd if k.startswith("mlp.") and k.endswith(".weight")})
    self.W = [sd[f"mlp.{i}.weight"].double().numpy() for i in idx]
    self.b = [sd[f"mlp.{i}.bias"].double().numpy() for i in idx]
    self.eps = eps

  def __call__(self, x):
    x = (np.asarray(x, np.float64) - self.mean) / (self.std + self.eps)
    for i, (W, b) in enumerate(zip(self.W, self.b)):
      x = x @ W.T + b
      if i < len(self.W) - 1:
        x = np.where(x > 0, x, np.expm1(np.minimum(x, 0)))
    return x


class MyNative:
  def __init__(self, mp, path=MJB):
    import mujoco
    self.mj = mujoco
    self.m = m = mujoco.MjModel.from_binary_path(str(path))
    self.d = mujoco.MjData(m)
    J = mujoco.mjtObj.mjOBJ_JOINT
    self.obs_joints = mp["entity_joint_names"]
    self.qadr = np.array([m.jnt_qposadr[mujoco.mj_name2id(m, J, "robot/" + n)] for n in self.obs_joints])
    self.dadr = np.array([m.jnt_dofadr[mujoco.mj_name2id(m, J, "robot/" + n)] for n in self.obs_joints])
    self.default = np.array(mp["default_joint_pos"])  # entity joint order
    act_names = mp["action_target_names"]
    self.scale = np.array(mp["action_scale"])
    self.offset = np.array(mp["action_offset"])
    # actuator i drives joint trnid -> its index in the action vector
    self.a_idx = np.array([act_names.index(mujoco.mj_id2name(m, J, int(m.actuator_trnid[i, 0])).split("/", 1)[1])
                           for i in range(m.nu)])
    self.site = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SITE, "robot/imu_in_pelvis")
    self.torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "robot/torso_link")
    self.decim = int(round(mp["step_dt"] / m.opt.timestep))

  def set_state(self, q, v, w=None):
    self.mj.mj_resetData(self.m, self.d)
    self.d.qpos[:] = q
    self.d.qvel[:] = v
    if w is not None:
      self.d.qacc_warmstart[:] = w
    self.mj.mj_forward(self.m, self.d)

  def obs_terms(self, last, cmd=np.zeros(3)):
    mj, m, d = self.mj, self.m, self.d
    res = np.zeros(6)
    mj.mj_objectVelocity(m, d, mj.mjtObj.mjOBJ_SITE, self.site, res, 1)  # [ang, lin] in site frame
    quat = d.qpos[3:7] / np.linalg.norm(d.qpos[3:7])
    qinv = np.array([quat[0], -quat[1], -quat[2], -quat[3]])
    g = np.zeros(3)
    mj.mju_rotVecQuat(g, np.array([0.0, 0.0, -1.0]), qinv)
    return {"base_lin_vel": res[3:6].copy(), "base_ang_vel": res[0:3].copy(), "projected_gravity": g,
            "joint_pos": d.qpos[self.qadr] - self.default, "joint_vel": d.qvel[self.dadr].copy(),
            "actions": np.asarray(last, float).copy(), "command": np.asarray(cmd, float)}

  def obs(self, last, order):
    t = self.obs_terms(last)
    return np.concatenate([t[k] for k in order])

  def ctrl(self, a):
    a = np.asarray(a, float)
    return (a * self.scale + self.offset)[self.a_idx]

  def step(self, a, n=None):
    self.d.ctrl[:] = self.ctrl(a)
    for _ in range(self.decim if n is None else n):
      self.mj.mj_step(self.m, self.d)
    self.mj.mj_forward(self.m, self.d)


# ------------------------------------------------------------------ metrics (own implementation of the stated definition)
def my_metrics(nat, qpos, qvel, pose, dt, names=("supine", "face_down", "side_roll+90", "side_roll-90")):
  """success: pelvis z > 0.70 and torso tilt < 15 deg continuously for 1 s. t_first = time of the first OK state of the
  first such window; t_report = the convention claimed in the report (start of window)."""
  mj = nat.mj
  T, n, _ = qpos.shape
  z = qpos[:, :, 2]
  tilt = np.zeros((T, n))
  for t in range(T):
    for e in range(n):
      nat.d.qpos[:] = qpos[t, e]
      mj.mj_kinematics(nat.m, nat.d)
      tilt[t, e] = np.degrees(np.arccos(np.clip(nat.d.xmat[nat.torso].reshape(3, 3)[2, 2], -1, 1)))
  ok = (z > 0.70) & (tilt < 15.0)
  H = int(round(1.0 / dt))
  t_first = np.full(n, np.nan)
  for e in range(n):
    for s in range(T - H + 1):
      if ok[s:s + H, e].all():
        t_first[e] = (s + 1) * dt
        break
  peak = np.abs(qvel[:, :, 6:]).max(axis=(0, 2))
  out = {}
  for grp, mask in [("overall", np.ones(n, bool))] + [(nm, pose == k) for k, nm in enumerate(names)]:
    if not mask.any():
      continue
    succ = ~np.isnan(t_first[mask])
    out[grp] = {"n": int(mask.sum()), "success": float(succ.mean()),
                "t_stand_first_ok_median": float(np.nanmedian(t_first[mask])) if succ.any() else None,
                "final_tilt_median_deg": float(np.median(tilt[-1, mask])),
                "final_z_median": float(np.median(z[-1, mask])),
                "peak_joint_speed_median": float(np.median(peak[mask])),
                "standing_end": float(ok[-1, mask].mean())}
  return out, t_first


# ------------------------------------------------------------------ mjlab env
def make_env(n, seed, balanced):
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  sys.path.insert(0, str(ROOT / "rl"))
  sys.path.insert(0, str(HERE))
  os.environ["GETUP_TASK"] = TASK
  os.environ["GETUP_KNOBS"] = str(KNOBS)
  import getup  # noqa: F401
  import mjlab.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.managers.event_manager import EventTermCfg
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  cfg = load_env_cfg(TASK, play=True)
  cfg.seed = seed
  cfg.scene.num_envs = n
  removed = [k for k, v in list(cfg.events.items()) if v.mode in ("startup", "interval")]
  for k in removed:
    cfg.events.pop(k)
  if balanced:
    from native_getup import balanced_lying_reset
    cfg.events["reset_base"] = EventTermCfg(func=balanced_lying_reset, mode="reset",
                                            params=dict(cfg.events["reset_base"].params))
  print("[env] removed", removed, "events", {k: (v.mode, getattr(v.func, "__name__", v.func)) for k, v in cfg.events.items()})
  print("[env] reset_base params", cfg.events["reset_base"].params)
  print("[env] decimation", cfg.decimation, "timestep", cfg.sim.mujoco.timestep)
  env = ManagerBasedRlEnv(cfg=cfg, device=DEV)
  agent = load_rl_cfg(TASK)
  print("[env] clip_actions", agent.clip_actions)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent), device=DEV)
  runner.load(str(POLICY), load_cfg={"actor": True}, strict=True, map_location=DEV)
  policy = runner.get_inference_policy(device=DEV)
  eps = None
  try:
    from rsl_rl.modules.normalization import EmpiricalNormalization
    mods = [mm for mm in runner.alg.actor.modules() if isinstance(mm, EmpiricalNormalization)]
    eps = [float(mm.eps) for mm in mods]
    print("[env] runner actor:", runner.alg.actor)
  except Exception as ex:  # noqa: BLE001
    print("[env] could not introspect actor:", repr(ex))
  return env, venv, policy, eps


def mapping_from_env(env):
  import torch
  r = env.scene["robot"]
  t = env.action_manager._terms["joint_pos"]
  sc = t._scale
  of = t._offset
  sc = (sc[0].cpu().numpy().tolist() if torch.is_tensor(sc) else [float(sc)] * t.action_dim)
  of = (of[0].cpu().numpy().tolist() if torch.is_tensor(of) else [float(of)] * t.action_dim)
  om = env.observation_manager
  terms = []
  for nm, dim, c in zip(om._group_obs_term_names["actor"], om._group_obs_term_dim["actor"],
                        om._group_obs_term_cfgs["actor"]):
    terms.append({"name": nm, "dim": list(dim), "func": c.func.__name__, "params": {k: str(v) for k, v in c.params.items()},
                  "noise": str(c.noise), "clip": str(c.clip), "scale": str(c.scale),
                  "history_length": c.history_length, "delay_max_lag": c.delay_max_lag})
  return {"entity_joint_names": list(r.joint_names), "action_target_names": list(t.target_names),
          "default_joint_pos": r.data.default_joint_pos[0].cpu().numpy().tolist(),
          "action_scale": sc, "action_offset": of, "action_class": type(t).__name__,
          "encoder_bias_max_abs": float(r.data.encoder_bias.abs().max()), "step_dt": float(env.step_dt),
          "actor_terms": terms, "actor_group_corruption": bool(om.cfg["actor"].enable_corruption)
          if hasattr(om, "cfg") and isinstance(om.cfg, dict) else "n/a"}


def phase_check(a):
  import mujoco
  import torch
  VOUT.mkdir(exist_ok=True)
  env, venv, policy, eps = make_env(a.n, a.seed, balanced=False)
  mp = mapping_from_env(env)
  info = json.loads((HERE / "models" / "getup_info.json").read_text())
  cross = {"info_joint_names_eq_entity": info["joint_names"] == mp["entity_joint_names"],
           "action_targets_eq_entity_order": mp["action_target_names"] == mp["entity_joint_names"],
           "info_default_max_abs": float(np.max(np.abs(np.array(info["default_joint_pos"]) - mp["default_joint_pos"]))),
           "info_scale_max_abs": float(np.max(np.abs(np.array(info["action_terms"]["joint_pos"]["scale"]) - mp["action_scale"]))),
           "info_offset_max_abs": float(np.max(np.abs(np.array(info["action_terms"]["joint_pos"]["offset"]) - mp["action_offset"]))),
           "normalizer_eps_runtime": eps}
  print("[check] mapping cross-check:", cross)
  print("[check] actor terms:", json.dumps(mp["actor_terms"], indent=1))
  (VOUT / "mapping.json").write_text(json.dumps(mp, indent=1))
  nat = MyNative(mp)
  from native_getup import CpuActor, NativeG1
  theirs = NativeG1()
  cpu_actor = CpuActor()
  np_actor = NpActor(eps=(eps[0] if eps else 1e-2))
  print("[check] checkpoint actor keys:", np_actor.keys)
  # model identity: runtime mj_model vs mjb
  mjm = env.sim.mj_model
  mcheck = {}
  for f in ("body_mass", "body_inertia", "body_ipos", "body_pos", "body_quat", "dof_armature", "dof_damping",
            "dof_frictionloss", "geom_friction", "geom_solref", "geom_solimp", "geom_size", "geom_margin", "geom_gap",
            "geom_condim", "geom_priority", "actuator_gainprm", "actuator_biasprm", "actuator_forcerange",
            "actuator_forcelimited", "actuator_ctrlrange", "actuator_ctrllimited", "jnt_range", "jnt_stiffness",
            "qpos0", "qpos_spring", "opt.timestep", "opt.integrator", "opt.cone", "opt.solver", "opt.iterations",
            "opt.ls_iterations", "opt.tolerance", "opt.impratio", "opt.noslip_iterations", "opt.o_margin",
            "opt.disableflags", "opt.enableflags"):
    x = eval("mjm." + f) if f.startswith("opt.") else getattr(mjm, f)
    y = eval("nat.m." + f) if f.startswith("opt.") else getattr(nat.m, f)
    mcheck[f] = float(np.max(np.abs(np.asarray(x, float) - np.asarray(y, float)))) if np.size(x) else 0.0
  print("[check] runtime model vs mjb:", {k: v for k, v in mcheck.items() if v != 0.0} or "all identical")
  sd = env.sim.data
  om = env.observation_manager
  order = om._group_obs_term_names["actor"]
  dims = [int(np.prod(d)) for d in om._group_obs_term_dim["actor"]]
  sl, i0 = {}, 0
  for nm, dm in zip(order, dims):
    sl[nm] = slice(i0, i0 + dm)
    i0 += dm
  rng = np.random.default_rng(a.seed)

  def snap():
    return (sd.qpos.cpu().numpy().astype(np.float64), sd.qvel.cpu().numpy().astype(np.float64),
            sd.qacc_warmstart.cpu().numpy().astype(np.float64))

  def write(q, v, w):
    sd.qpos[:] = torch.as_tensor(q, dtype=sd.qpos.dtype, device=DEV)
    sd.qvel[:] = torch.as_tensor(v, dtype=sd.qvel.dtype, device=DEV)
    sd.qacc_warmstart[:] = torch.as_tensor(w, dtype=sd.qacc_warmstart.dtype, device=DEV)

  def mj_steps(q, v, w, act, k):
    write(q, v, w)
    env.action_manager.process_action(act)
    for _ in range(k):
      env.action_manager.apply_action()
      env.scene.write_data_to_sim()
      env.sim.step()
    out = snap()
    return out[0], out[1], sd.ctrl.cpu().numpy().astype(np.float64)

  T, PUSH = a.steps, a.push_step
  check_steps = sorted(set(int(x) for x in a.check_steps.split(",")))
  env.reset()
  obs = venv.get_observations()
  records = []
  origins = env.scene.env_origins.cpu().numpy()
  for s in range(T):
    pushed = False
    if s == PUSH:  # random push + joint perturbation, written into mjlab, obs recomputed by mjlab
      q, v, w = snap()
      jr = nat.m.jnt_range[1:]  # hinge joints (joint 0 = free)
      qadr = nat.m.jnt_qposadr[1:]
      q[:, qadr] = np.clip(q[:, qadr] + rng.uniform(-0.3, 0.3, (a.n, len(qadr))), jr[:, 0] + a.clip_margin,
                           jr[:, 1] - a.clip_margin)
      v[:, 0:3] += rng.uniform(-1.0, 1.0, (a.n, 3))
      v[:, 3:6] += rng.uniform(-2.0, 2.0, (a.n, 3))
      v[:, 6:] += rng.normal(0, 1.5, (a.n, v.shape[1] - 6))
      write(q, v, w)
      env.sim.forward()
      from tensordict import TensorDict
      # NB: venv.get_observations() returns the CACHED obs (ObservationManager.compute(update_history=False))
      obs = TensorDict(env.observation_manager.compute(update_history=True), batch_size=[a.n])
      pushed = True
    if s in check_steps or pushed:
      q, v, w = snap()
      o = obs["actor"].cpu().numpy().astype(np.float64)
      last = env.action_manager.action.cpu().numpy().astype(np.float64)
      cmd = env.command_manager.get_command("twist").cpu().numpy().astype(np.float64)
      with torch.no_grad():
        act_t = policy(obs)
      act = act_t.cpu().numpy().astype(np.float64)
      rec = {"step": s, "pushed": pushed, "cmd_max_abs": float(np.abs(cmd).max()), "term_max": {}, "term_max_theirs": {},
             "imu_sensor_vs_objvel": 0.0}
      nat_obs = np.zeros_like(o)
      for e in range(a.n):
        nat.set_state(q[e], v[e])
        tt = nat.obs_terms(last[e])
        nat_obs[e] = np.concatenate([tt[k] for k in order])
        sadr = {nat.m.sensor(i).name: int(nat.m.sensor_adr[i]) for i in range(nat.m.nsensor)}
        sens = np.concatenate([nat.d.sensordata[sadr["robot/imu_lin_vel"]:sadr["robot/imu_lin_vel"] + 3],
                               nat.d.sensordata[sadr["robot/imu_ang_vel"]:sadr["robot/imu_ang_vel"] + 3]])
        rec["imu_sensor_vs_objvel"] = max(rec["imu_sensor_vs_objvel"],
                                          float(np.abs(sens - np.concatenate([tt["base_lin_vel"], tt["base_ang_vel"]])).max()))
        theirs.set_state(q[e], v[e])
        ot = theirs.obs(last[e])
        for k in order:
          rec["term_max"][k] = max(rec["term_max"].get(k, 0.0), float(np.abs(nat_obs[e, sl[k]] - o[e, sl[k]]).max()))
          rec["term_max_theirs"][k] = max(rec["term_max_theirs"].get(k, 0.0), float(np.abs(ot[sl[k]] - o[e, sl[k]]).max()))
      a_np_mj = np_actor(o)
      a_np_nat = np_actor(nat_obs)
      rec["act_runner_vs_np(mjlab obs)"] = float(np.abs(a_np_mj - act).max())
      rec["act_runner_vs_theirCpuActor(mjlab obs)"] = float(np.abs(cpu_actor(o) - act).max())
      rec["act_runner(mjlab obs)_vs_np(native obs)"] = float(np.abs(a_np_nat - act).max())
      rec["obs_abs_max"] = float(np.abs(o).max())
      # physics: 1 substep and 1 env step (decimation substeps), same state + warm start + action
      for k, tag in ((1, "substep"), (nat.decim, "envstep")):
        q1, v1, ctrl = mj_steps(q, v, w, act_t, k)
        dq, dv, dc = [], [], []
        for e in range(a.n):
          nat.set_state(q[e], v[e], w[e])
          nat.d.ctrl[:] = nat.ctrl(act[e])
          dc.append(float(np.abs(nat.d.ctrl - ctrl[e]).max()))
          for _ in range(k):
            mujoco.mj_step(nat.m, nat.d)
          dq.append(float(np.abs(nat.d.qpos - q1[e]).max()))
          dv.append(float(np.abs(nat.d.qvel - v1[e]).max()))
          if k == 1 and (pushed or s == 0) and e < 4:
            j = int(np.abs(nat.d.qvel - v1[e]).argmax())
            jn = [nat.m.joint(i).name for i in range(nat.m.njnt) if nat.m.jnt_dofadr[i] <= j][-1]
            print(f"   [diag step {s} env {e}] worst dof {j} ({jn}) native {nat.d.qvel[j]:+.3f} warp {v1[e][j]:+.3f}"
                  f" | native ncon {nat.d.ncon} nefc {nat.d.nefc} | solver niter {int(nat.d.solver_niter[0])}")
        rec[f"{tag}_dq_max"], rec[f"{tag}_dq_median"] = max(dq), float(np.median(dq))
        rec[f"{tag}_dv_max"], rec[f"{tag}_dv_median"] = max(dv), float(np.median(dv))
        rec["ctrl_max_abs_diff"] = max(rec.get("ctrl_max_abs_diff", 0.0), max(dc))
      # native solver self-convergence on the same substep: nominal (10 it) vs 200 iterations / 50 ls iterations
      it0, ls0 = nat.m.opt.iterations, nat.m.opt.ls_iterations
      dconv = []
      for e in range(a.n):
        res_ = []
        for it, ls in ((it0, ls0), (200, 50)):
          nat.m.opt.iterations, nat.m.opt.ls_iterations = it, ls
          nat.set_state(q[e], v[e], w[e])
          nat.d.ctrl[:] = nat.ctrl(act[e])
          mujoco.mj_step(nat.m, nat.d)
          res_.append(nat.d.qvel.copy())
        dconv.append(float(np.abs(res_[0] - res_[1]).max()))
      nat.m.opt.iterations, nat.m.opt.ls_iterations = it0, ls0
      rec["native_substep_self_convergence_dv_max"] = max(dconv)
      rec["native_substep_self_convergence_dv_median"] = float(np.median(dconv))
      write(q, v, w)  # restore, continue the mjlab rollout normally
      env.sim.forward()
      records.append(rec)
      print(f"[check] step {s}{' (after push)' if pushed else ''}: obs term max " +
            ", ".join(f"{k} {rec['term_max'][k]:.1e}" for k in order) +
            f" | act np(native obs) vs runner {rec['act_runner(mjlab obs)_vs_np(native obs)']:.1e}"
            f" | ctrl {rec['ctrl_max_abs_diff']:.1e} | substep dv max {rec['substep_dv_max']:.2e} med "
            f"{rec['substep_dv_median']:.1e} | envstep dq max {rec['envstep_dq_max']:.2e} | native self-conv dv max "
            f"{rec['native_substep_self_convergence_dv_max']:.2e} med {rec['native_substep_self_convergence_dv_median']:.1e}",
            flush=True)
    else:
      with torch.no_grad():
        act_t = policy(obs)
    with torch.no_grad():
      obs, _, _, _ = venv.step(act_t)
  summ = {"seed": a.seed, "n": a.n, "push_step": PUSH, "check_steps": check_steps, "mapping_cross_check": cross,
          "model_check": mcheck, "records": records,
          "overall_term_max": {k: max(r["term_max"][k] for r in records) for k in order},
          "overall_term_max_theirs_NativeG1": {k: max(r["term_max_theirs"][k] for r in records) for k in order}}
  (VOUT / f"check_seed{a.seed}.json").write_text(json.dumps(summ, indent=1))
  print("[check] overall per-term max |diff| (my native):", summ["overall_term_max"])
  print("[check] overall per-term max |diff| (their NativeG1):", summ["overall_term_max_theirs_NativeG1"])
  print("[check] wrote", VOUT / f"check_seed{a.seed}.json")


def phase_closed(a):
  import torch
  VOUT.mkdir(exist_ok=True)
  env, venv, policy, eps = make_env(a.n, a.seed, balanced=True)
  mp = mapping_from_env(env)
  sd = env.sim.data
  env.reset()
  obs = venv.get_observations()
  origins = env.scene.env_origins.cpu().numpy().astype(np.float64)
  pose = env._getup_pose.cpu().numpy().copy()
  q0 = sd.qpos.cpu().numpy().astype(np.float64)
  v0 = sd.qvel.cpu().numpy().astype(np.float64)
  q0[:, 0:2] -= origins[:, 0:2]
  T = a.steps
  qm = np.zeros((T, a.n, q0.shape[1]))
  vm = np.zeros((T, a.n, v0.shape[1]))
  t0 = time.time()
  for s in range(T):
    with torch.no_grad():
      act = policy(obs)
      obs, _, _, _ = venv.step(act)
    q = sd.qpos.cpu().numpy().astype(np.float64)
    q[:, 0:2] -= origins[:, 0:2]
    qm[s], vm[s] = q, sd.qvel.cpu().numpy().astype(np.float64)
  print(f"[closed] mjlab {a.n} x {T} steps in {time.time() - t0:.0f}s")
  nat = MyNative(mp)
  actor = NpActor(eps=(eps[0] if eps else 1e-2))
  order = env.observation_manager._group_obs_term_names["actor"]
  qn = np.zeros_like(qm)
  vn = np.zeros_like(vm)
  t0 = time.time()
  for e in range(a.n):
    nat.set_state(q0[e], v0[e])
    last = np.zeros(29)
    for s in range(T):
      act = actor(nat.obs(last, order))
      nat.step(act)
      last = act
      qn[s, e], vn[s, e] = nat.d.qpos, nat.d.qvel
  print(f"[closed] my native {a.n} x {T} steps in {time.time() - t0:.0f}s")
  dt = float(env.step_dt)
  res = {"seed": a.seed, "n": a.n, "pose": pose.tolist()}
  for tag, (qq, vv) in (("mjlab", (qm, vm)), ("my_native", (qn, vn))):
    res[tag], tf = my_metrics(nat, qq, vv, pose, dt)
    res[tag + "_t_first"] = tf.tolist()
  jr = np.sqrt(np.mean((qm[:, :, 7:] - qn[:, :, 7:]) ** 2, axis=2))
  rp = np.linalg.norm(qm[:, :, 0:3] - qn[:, :, 0:3], axis=2)
  res["divergence"] = {f"{(s + 1) * dt:.2f}": {"joint_rms_median": float(np.median(jr[s])), "joint_rms_max": float(jr[s].max()),
                                               "root_pos_median": float(np.median(rp[s])), "root_pos_max": float(rp[s].max())}
                       for s in (0, 4, 49, 99, 249, T - 1) if s < T}
  # their metric function on my logs (consistency of definitions)
  sys.path.insert(0, str(HERE))
  from native_getup import NativeG1, metrics
  their_m = {tag: metrics(NativeG1(), qq, vv, pose, dt)[0] for tag, (qq, vv) in (("mjlab", (qm, vm)), ("my_native", (qn, vn)))}
  res["their_metrics_fn"] = their_m
  np.savez_compressed(VOUT / f"closed_seed{a.seed}.npz", qm=qm, vm=vm, qn=qn, vn=vn, pose=pose, q0=q0, v0=v0)
  (VOUT / f"closed_seed{a.seed}.json").write_text(json.dumps(res, indent=1))
  print(json.dumps({k: res[k] for k in ("mjlab", "my_native", "divergence")}, indent=1))
  print("[closed] their metrics fn overall:", {t: v["overall"] for t, v in their_m.items()})


def phase_replay(a):
  """My native implementation from THEIR seed-0 initial states (out/getup_mjlab.npz); compare with their native log
  and recompute the md headline metrics from their npz logs with my metric code."""
  mp = json.loads((VOUT / "mapping.json").read_text())
  ref = np.load(HERE / "out" / "getup_mjlab.npz")
  their = np.load(HERE / "out" / "getup_native.npz")
  nat = MyNative(mp)
  actor = NpActor()
  order = [t["name"] for t in mp["actor_terms"]]
  n, T = ref["init_qpos"].shape[0], ref["qpos"].shape[0]
  qn = np.zeros_like(their["qpos"])
  vn = np.zeros_like(their["qvel"])
  t0 = time.time()
  for e in range(n):
    nat.set_state(ref["init_qpos"][e], ref["init_qvel"][e])
    last = np.zeros(29)
    for s in range(T):
      act = actor(nat.obs(last, order))
      nat.step(act)
      last = act
      qn[s, e], vn[s, e] = nat.d.qpos, nat.d.qvel
  print(f"[replay] my native {n} x {T} in {time.time() - t0:.0f}s")
  dt = float(ref["dt"])
  d = np.abs(qn - their["qpos"]).max(axis=2)  # (T, n)
  out = {"my_native_vs_their_native_qpos_maxabs": {"t=0.02": float(d[0].max()), "t=0.1": float(d[4].max()),
                                                   "t=1": float(d[49].max()), "t=10": float(d[-1].max()),
                                                   "max_over_all": float(d.max()),
                                                   "median_final": float(np.median(d[-1]))}}
  res = {}
  for tag, qq, vv in (("mjlab", ref["qpos"], ref["qvel"]), ("their_native", their["qpos"], their["qvel"]),
                      ("my_native", qn, vn)):
    res[tag], _ = my_metrics(nat, qq, vv, ref["pose"], dt)
  out["metrics_seed0_my_code"] = res
  # their divergence table entry at t=0.02 (their stats): first-step joint rms of their native vs mjlab
  jr = np.sqrt(np.mean((ref["qpos"][:, :, 7:] - their["qpos"][:, :, 7:]) ** 2, axis=2))
  out["their_native_vs_mjlab_joint_rms"] = {f"{(s + 1) * dt:.2f}": [float(np.median(jr[s])), float(jr[s].max())]
                                            for s in (0, 1, 4, 49, 99, 499)}
  (VOUT / "replay_seed0.json").write_text(json.dumps(out, indent=1))
  print(json.dumps(out, indent=1))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("phase", choices=["check", "closed", "replay"])
  ap.add_argument("--n", type=int, default=None)
  ap.add_argument("--seed", type=int, default=None)
  ap.add_argument("--steps", type=int, default=None)
  ap.add_argument("--push_step", type=int, default=200)
  ap.add_argument("--clip_margin", type=float, default=0.02)
  ap.add_argument("--check_steps", default="0,37,120,199,201,205,230,260,299")
  a = ap.parse_args()
  if a.phase == "check":
    a.n, a.seed, a.steps = a.n or 32, 123 if a.seed is None else a.seed, a.steps or 300
  elif a.phase == "closed":
    a.n, a.seed, a.steps = a.n or 16, 1 if a.seed is None else a.seed, a.steps or 500
  {"check": phase_check, "closed": phase_closed, "replay": phase_replay}[a.phase](a)
