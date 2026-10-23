"""Sim2sim for the G1 get-up policy (getup_auto_r08, task Dance-Recovery-G1-auto): mjlab (mujoco_warp, GPU) vs
native MuJoCo (C library, CPU), from the SAME initial states, with NO randomisation in either simulator.

Phases (run in this order; native_getup.sh runs all of them):
  python native_getup.py mjlab  [--n 64] [--steps 500] [--seed 0]
      unitree_rl_mjlab env + GPU. Builds the play env with the startup randomisation events removed
      (encoder_bias, foot_friction, base_com), resets N envs into the 4 fallen poses (balanced: env i gets pose i % 4,
      same reset function reset_root_state_mixed of the task), records qpos/qvel right after the reset, rolls the
      trained policy (rsl_rl runner, as eval_getup.py) for --steps policy steps and logs the trajectory.
      At EVERY step it also runs the equivalence test: the full mjlab state of every env is copied into a native
      MjData and the native observation (computed by NativeG1.obs below) is compared term by term with mjlab's actor
      observation; the CPU re-implementation of the actor is compared with the runner's policy on the same input;
      the native action->ctrl mapping is compared with mjlab's ctrl; and one ENV step (4 physics substeps) is
      re-simulated natively from the pre-step state (qpos, qvel, qacc_warmstart) + the same action and compared with
      mjlab's post-step state. Afterwards, single PHYSICS substeps are compared (state written into both sims).
      -> out/getup_mjlab.npz
  python native_getup.py native [--model models/getup.mjb] [--tag native]
      Pure MuJoCo + torch (CPU, no mjlab import). Runs the policy fully inside native MuJoCo from the recorded initial
      states: obs -> CPU actor (obs normaliser + MLP, deterministic mean) -> ctrl = a * scale + default_pos (joint
      order, mapped to actuator order) -> 4 x mj_step -> mj_forward (mirrors mjlab's single forward() before obs).
      With --model models/getup.xml it loads the XML exported from the scene spec (meshes from mjlab's G1 asset dir,
      solver options from out/getup_opt.json), e.g. for the MuJoCo 3.16 cross-version check in the gmr env.
      -> out/getup_<tag>.npz
  python native_getup.py report
      Metrics for every simulator log found, trajectory divergence vs mjlab, results_getup.json / results_getup.md,
      side-by-side video ../videos/sim2sim/getup_side_by_side.mp4 (mjlab trajectory replayed left, native right).
"""
import argparse
import json
import os
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
POLICY = ROOT / "policies" / "getup_auto_r08" / "policy.pt"
KNOBS = ROOT / "policies" / "getup_auto_r08" / "knobs.json"
OUT = HERE / "out"
VIDEO_DIR = ROOT / "videos" / "sim2sim"
TASK = "Dance-Recovery-G1-auto"
INFO = json.loads((HERE / "models" / "getup_info.json").read_text())
TERMS = [("base_lin_vel", 3), ("base_ang_vel", 3), ("projected_gravity", 3), ("joint_pos", 29), ("joint_vel", 29),
         ("actions", 29), ("command", 3)]
POSE_NAMES = ["supine", "face_down", "side_roll+90", "side_roll-90"]
OPT_FIELDS = ("timestep", "integrator", "cone", "jacobian", "solver", "iterations", "tolerance", "ls_iterations",
              "ls_tolerance", "ccd_iterations", "impratio", "gravity", "enableflags", "disableflags")
FP_FIELDS = ("body_mass", "body_inertia", "body_ipos", "body_pos", "body_quat", "dof_armature", "dof_damping",
             "dof_frictionloss", "geom_friction", "geom_solref", "geom_solimp", "geom_size", "geom_pos", "geom_type",
             "geom_contype", "geom_conaffinity", "actuator_gainprm", "actuator_biasprm", "actuator_forcerange",
             "actuator_trnid", "jnt_range", "qpos0")
G1_ASSETS = Path.home() / "miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab/asset_zoo/robots/unitree_g1/xmls/assets"


def term_slices():
  out, i = {}, 0
  for name, n in TERMS:
    out[name] = slice(i, i + n)
    i += n
  return out


# ----------------------------------------------------------------------------------------------------------------
# CPU actor: rsl_rl 5.0.1 MLPModel with EmpiricalNormalization (eps 1e-2), ELU, deterministic output (mean)
# ----------------------------------------------------------------------------------------------------------------
class CpuActor:
  def __init__(self, path=POLICY):
    import torch
    torch.set_num_threads(1)
    self.torch = torch
    sd = torch.load(path, weights_only=False, map_location="cpu")["actor_state_dict"]
    self.mean = sd["obs_normalizer._mean"].float()
    self.std = sd["obs_normalizer._std"].float()
    self.eps = 1e-2
    nn = torch.nn
    self.net = nn.Sequential(nn.Linear(99, 512), nn.ELU(), nn.Linear(512, 256), nn.ELU(), nn.Linear(256, 128), nn.ELU(),
                             nn.Linear(128, 29))
    self.net.load_state_dict({k.replace("mlp.", ""): v for k, v in sd.items() if k.startswith("mlp.")})
    self.net.eval()

  def __call__(self, obs):
    with self.torch.no_grad():
      x = self.torch.as_tensor(np.asarray(obs, dtype=np.float32)).reshape(-1, 99)
      return self.net((x - self.mean) / (self.std + self.eps)).numpy().astype(np.float64)


# ----------------------------------------------------------------------------------------------------------------
# Native MuJoCo G1: observation, action -> ctrl, stepping (no mjlab)
# ----------------------------------------------------------------------------------------------------------------
def load_model(path):
  import mujoco
  path = Path(path)
  if path.suffix == ".mjb":
    return mujoco.MjModel.from_binary_path(str(path))
  import re
  xml = path.read_text()
  # spec.to_xml() of the mjlab scene writes an empty, unnamed <default/> that the XML parser rejects
  xml = re.sub(r"\n\s*<default/>", "", xml)
  assets = {}
  for f in set(re.findall(r'file="([^"]+)"', xml)):
    src = G1_ASSETS / Path(f).name
    if src.exists():
      assets[f] = src.read_bytes()
  m = mujoco.MjModel.from_xml_string(xml, assets)
  opt = json.loads((OUT / "getup_opt.json").read_text())  # solver options mjlab applies after compile (not in XML)
  for k, v in opt.items():
    if k == "gravity":
      m.opt.gravity[:] = v
    else:
      setattr(m.opt, k, type(getattr(m.opt, k))(v))
  return m


class NativeG1:
  def __init__(self, model_path=HERE / "models" / "getup.mjb"):
    import mujoco
    self.mj = mujoco
    self.m = m = load_model(model_path)
    self.d = mujoco.MjData(m)
    names = INFO["joint_names"]
    self.qadr = np.array([m.jnt_qposadr[m.joint("robot/" + n).id] for n in names])
    self.dadr = np.array([m.jnt_dofadr[m.joint("robot/" + n).id] for n in names])
    self.default = np.array(INFO["default_joint_pos"])
    jp = INFO["action_terms"]["joint_pos"]
    assert jp["class"] == "JointPositionAction"
    self.scale, self.offset = np.array(jp["scale"]), np.array(jp["offset"])
    self.act2joint = np.array([names.index(m.joint(int(m.actuator_trnid[i, 0])).name.split("/", 1)[1])
                               for i in range(m.nu)])
    sadr = {m.sensor(i).name: int(m.sensor_adr[i]) for i in range(m.nsensor)}
    self.s_lin, self.s_ang = sadr["robot/imu_lin_vel"], sadr["robot/imu_ang_vel"]
    self.pelvis = m.body("robot/pelvis").id
    self.torso = m.body("robot/torso_link").id
    self.decim = int(INFO["decimation"])
    assert abs(m.opt.timestep - INFO["timestep"]) < 1e-12, m.opt.timestep

  def set_state(self, qpos, qvel, qacc_warmstart=None):
    mj, d = self.mj, self.d
    mj.mj_resetData(self.m, d)
    d.qpos[:] = qpos
    d.qvel[:] = qvel
    if qacc_warmstart is not None:
      d.qacc_warmstart[:] = qacc_warmstart
    mj.mj_forward(self.m, d)

  def ctrl_from_action(self, a):
    """JointPositionAction: target = raw * scale + default (joint order); builtin position actuators: ctrl = target."""
    return (np.asarray(a) * self.scale + self.offset)[self.act2joint]

  def step(self, a, substeps=None):
    self.d.ctrl[:] = self.ctrl_from_action(a)
    for _ in range(self.decim if substeps is None else substeps):
      self.mj.mj_step(self.m, self.d)
    self.mj.mj_forward(self.m, self.d)  # mjlab calls sim.forward() once before computing observations

  def obs(self, last_action, command=(0.0, 0.0, 0.0)):
    """Actor obs (99), mjlab definitions (verified in mjlab source):
    base_lin_vel / base_ang_vel = builtin sensors robot/imu_lin_vel (velocimeter) / robot/imu_ang_vel (gyro) at site
    imu_in_pelvis, site frame; projected_gravity = R(pelvis xquat)^T (0,0,-1) (root LINK frame, not COM);
    joint_pos = q - default (no encoder bias: joint_pos_rel(biased=False)); joint_vel = qd - 0; actions = last raw
    policy action; command = twist command (zero in this task). No scale / clip / noise (play: corruption off)."""
    d = self.d
    g = -d.xmat[self.pelvis].reshape(3, 3)[2, :]  # R^T @ (0, 0, -1)
    return np.concatenate([d.sensordata[self.s_lin:self.s_lin + 3], d.sensordata[self.s_ang:self.s_ang + 3], g,
                           d.qpos[self.qadr] - self.default, d.qvel[self.dadr], np.asarray(last_action),
                           np.asarray(command)])


# ----------------------------------------------------------------------------------------------------------------
# Phase 1: mjlab reference rollout + equivalence test
# ----------------------------------------------------------------------------------------------------------------
def balanced_lying_reset(env, env_ids, stand_prob=0.0, stand_height=0.76, height_range=(0.08, 0.15),
                         yaw_range=(-3.14, 3.14), asset_cfg=None, pose=None, pose_extra=(0.0, 0.0, 0.0, 0.0),
                         true_supine=False, squat_prob=0.0, squat_height=0.50, squat_t0=0.0):
  """The task's own reset_root_state_mixed, with the fallen pose forced to env_id % 4 (16 of each for 64 envs)."""
  import torch
  from getup.mdp import reset_root_state_mixed
  if env_ids is None:
    env_ids = torch.arange(env.num_envs, device=env.device, dtype=torch.int64)
  for k in range(4):
    ids = env_ids[env_ids % 4 == k]
    if len(ids):
      reset_root_state_mixed(env, ids, stand_prob=stand_prob, stand_height=stand_height, height_range=height_range,
                             yaw_range=yaw_range, asset_cfg=asset_cfg, pose=k, pose_extra=pose_extra,
                             true_supine=true_supine, squat_prob=squat_prob, squat_height=squat_height,
                             squat_t0=squat_t0)


def phase_mjlab(a):
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  sys.path.insert(0, str(ROOT / "rl"))
  os.environ["GETUP_TASK"] = TASK
  os.environ["GETUP_KNOBS"] = str(KNOBS)
  from dataclasses import asdict

  import mujoco
  import torch

  import getup  # noqa: F401
  import mjlab.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.managers.event_manager import EventTermCfg
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  OUT.mkdir(exist_ok=True)
  dev = "cuda:0"
  cfg = load_env_cfg(TASK, play=True)
  cfg.seed = a.seed
  cfg.scene.num_envs = a.n
  removed = [k for k, v in list(cfg.events.items()) if v.mode in ("startup", "interval")]
  for k in removed:
    cfg.events.pop(k)
  rb = cfg.events["reset_base"]
  assert rb.func.__name__ == "reset_root_state_mixed", rb.func
  assert rb.params.get("stand_prob", 0) == 0 and rb.params.get("squat_prob", 0) == 0, rb.params
  cfg.events["reset_base"] = EventTermCfg(func=balanced_lying_reset, mode="reset", params=dict(rb.params))
  print("[mjlab] removed events:", removed, "| remaining:", {k: v.mode for k, v in cfg.events.items()})
  print("[mjlab] terminations:", list(cfg.terminations), "episode_length_s", cfg.episode_length_s)

  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(str(POLICY), load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  actor = CpuActor()
  nat = NativeG1()
  sd = env.sim.data
  mjm = env.sim.mj_model
  # the native model must be the very model mjlab runs (sizes + option + a few physics arrays)
  for f in ("nq", "nv", "nu", "nbody", "ngeom"):
    assert getattr(mjm, f) == getattr(nat.m, f), f
  model_check = {f: float(np.max(np.abs(getattr(mjm, f) - getattr(nat.m, f)))) for f in (
    "body_mass", "body_inertia", "body_ipos", "dof_armature", "dof_damping", "dof_frictionloss", "geom_friction",
    "geom_solref", "geom_solimp", "actuator_gainprm", "actuator_biasprm", "actuator_forcerange", "jnt_range")}
  opt = {k: (getattr(mjm.opt, k).tolist() if k == "gravity" else getattr(mjm.opt, k).item()
             if hasattr(getattr(mjm.opt, k), "item") else getattr(mjm.opt, k)) for k in OPT_FIELDS}
  opt_native = {k: (getattr(nat.m.opt, k).tolist() if k == "gravity" else getattr(nat.m.opt, k).item()
                    if hasattr(getattr(nat.m.opt, k), "item") else getattr(nat.m.opt, k)) for k in OPT_FIELDS}
  assert opt == opt_native, (opt, opt_native)
  (OUT / "getup_opt.json").write_text(json.dumps({k: (int(v) if isinstance(v, (bool, int)) else v) for k, v in opt.items()}, indent=1))
  print("[mjlab] model check (max |mjlab runtime model - exported mjb|):", model_check)
  wpo = env.sim.wp_model.opt
  warp_opt = {k: str(getattr(wpo, k)) for k in ("ls_parallel", "contact_sensor_maxmatch") if hasattr(wpo, k)}

  env.reset()
  obs = venv.get_observations()
  origins = env.scene.env_origins.cpu().numpy().astype(np.float64)
  pose = env._getup_pose.cpu().numpy().copy()
  n, T = a.n, a.steps

  def snap():
    return (sd.qpos.cpu().numpy().astype(np.float64), sd.qvel.cpu().numpy().astype(np.float64),
            sd.qacc_warmstart.cpu().numpy().astype(np.float64))

  q0, v0, _ = snap()
  off = np.zeros(mjm.nq)
  init_qpos = q0.copy()
  init_qpos[:, 0:2] -= origins[:, 0:2]
  sl = term_slices()
  obs_max = {k: 0.0 for k, _ in TERMS}
  obs_hist = {k: [] for k, _ in TERMS}  # per-step max over envs
  act_diff, ctrl_diff = [], []
  phys_dq, phys_dv = [], []  # per (step, env) max |diff| after one env step (4 substeps)
  qlog = np.zeros((T, n, mjm.nq))
  vlog = np.zeros((T, n, mjm.nv))
  alog = np.zeros((T, n, 29))
  sub_steps = sorted(set(s for s in (0, 1, 5, 25, 50, 100, 200, 300, 400) if s < T))
  sub_snap = {}

  # the native side keeps its OWN last action (zeros after reset, then the raw policy action it was given), as in the
  # native closed loop; it is NOT read from mjlab's action manager, so the 'actions' term tests mjlab's last_action
  # semantics (raw vs processed / clipped / scaled, reset value) instead of comparing a copy with itself
  nat_last = np.zeros((n, 29))

  def compare_obs():
    o = obs["actor"].cpu().numpy().astype(np.float64)
    q, v, _ = snap()
    cmd = env.command_manager.get_command("twist").cpu().numpy().astype(np.float64)
    step_max = {k: 0.0 for k, _ in TERMS}
    for e in range(n):
      nat.set_state(q[e], v[e])
      on = nat.obs(nat_last[e])  # command: native uses the constant zero command
      for k, _ in TERMS:
        dk = float(np.max(np.abs(on[sl[k]] - o[e, sl[k]])))
        step_max[k] = max(step_max[k], dk)
    for k in step_max:
      obs_max[k] = max(obs_max[k], step_max[k])
      obs_hist[k].append(step_max[k])
    return float(np.max(np.abs(cmd)))

  cmd_max = compare_obs()
  t0 = time.time()
  for s in range(T):
    qpre, vpre, wpre = snap()
    with torch.no_grad():
      act = policy(obs)
    act_np = act.cpu().numpy().astype(np.float64)
    act_diff.append(float(np.max(np.abs(actor(obs["actor"].cpu().numpy()) - act_np))))
    if s in sub_snap or s in sub_steps:
      sub_snap[s] = (qpre, vpre, wpre, act.clone())
    with torch.no_grad():
      obs, _, _, _ = venv.step(act)
    qpost, vpost, _ = snap()
    ctrl = sd.ctrl.cpu().numpy().astype(np.float64)
    for e in range(n):
      ctrl_diff.append(float(np.max(np.abs(nat.ctrl_from_action(act_np[e]) - ctrl[e]))))
      nat.set_state(qpre[e], vpre[e], wpre[e])
      nat.step(act_np[e])
      phys_dq.append(float(np.max(np.abs(nat.d.qpos - qpost[e]))))
      phys_dv.append(float(np.max(np.abs(nat.d.qvel - vpost[e]))))
    nat_last[:] = act_np
    cmd_max = max(cmd_max, compare_obs())
    q = qpost.copy()
    q[:, 0:2] -= origins[:, 0:2]
    qlog[s], vlog[s], alog[s] = q, vpost, act_np
    if s % 100 == 0:
      print(f"[mjlab] step {s}/{T}  obs max|diff| so far {max(obs_max.values()):.2e}  env-step |dq| max "
            f"{max(phys_dq):.2e}  ({time.time() - t0:.0f}s)", flush=True)

  # single PHYSICS substep: write the same state + action into both sims and step once
  sub_dq, sub_dv = [], []
  for s in sub_steps:
    qpre, vpre, wpre, act = sub_snap[s]
    sd.qpos[:] = torch.as_tensor(qpre, dtype=sd.qpos.dtype, device=dev)
    sd.qvel[:] = torch.as_tensor(vpre, dtype=sd.qvel.dtype, device=dev)
    sd.qacc_warmstart[:] = torch.as_tensor(wpre, dtype=sd.qacc_warmstart.dtype, device=dev)
    env.action_manager.process_action(act)
    env.action_manager.apply_action()
    env.scene.write_data_to_sim()
    env.sim.step()
    q1, v1, _ = snap()
    act_np = act.cpu().numpy().astype(np.float64)
    for e in range(n):
      nat.set_state(qpre[e], vpre[e], wpre[e])
      nat.d.ctrl[:] = nat.ctrl_from_action(act_np[e])
      mujoco.mj_step(nat.m, nat.d)
      sub_dq.append(float(np.max(np.abs(nat.d.qpos - q1[e]))))
      sub_dv.append(float(np.max(np.abs(nat.d.qvel - v1[e]))))

  def dist(x):
    x = np.asarray(x)
    return {"max": float(x.max()), "p99": float(np.percentile(x, 99)), "median": float(np.median(x)),
            "n": int(x.size)}

  phys_dq_a = np.array(phys_dq).reshape(T, n)
  phys_dv_a = np.array(phys_dv).reshape(T, n)
  equiv = {
    "n_envs": n, "n_steps": T, "obs_compared_states": n * (T + 1),
    "obs_max_abs_diff": obs_max, "obs_term_pass_1e-4": {k: bool(v < 1e-4) for k, v in obs_max.items()},
    "obs_term_what_is_tested": {
      "base_lin_vel": "native velocimeter sensor recomputed by mj_forward from the copied qpos/qvel",
      "base_ang_vel": "native gyro sensor recomputed by mj_forward from the copied qpos/qvel",
      "projected_gravity": "native pelvis rotation (mj_kinematics) from the copied qpos",
      "joint_pos": "copied qpos -> joint order (name lookup) minus default_joint_pos from getup_info.json",
      "joint_vel": "copied qvel -> joint order only (no arithmetic, so exact 0 means the index mapping is right; "
                   "it cannot detect a velocity-estimation problem)",
      "actions": "native-maintained last raw action (zeros at reset) vs mjlab's last_action term",
      "command": "native constant zero vs mjlab's generated_commands(twist); trivial: the command is identically "
                 "zero in this task (see mjlab_command_max_abs)"},
    "mjlab_command_max_abs": cmd_max,
    "actor_cpu_vs_runner_max_abs_diff": float(max(act_diff)),
    "ctrl_native_vs_mjlab_max_abs_diff": float(max(ctrl_diff)),
    "env_step_4_substeps": {"qpos": dist(phys_dq), "qvel": dist(phys_dv),
                            "first_step_qpos_max": float(phys_dq_a[0].max()),
                            "first_step_qvel_max": float(phys_dv_a[0].max()),
                            "qpos_median_per_second": [float(np.median(phys_dq_a[i:i + 50])) for i in range(0, T, 50)],
                            "qvel_median_per_second": [float(np.median(phys_dv_a[i:i + 50])) for i in range(0, T, 50)]},
    "single_substep": {"steps_sampled": sub_steps, "qpos": dist(sub_dq), "qvel": dist(sub_dv)},
    "model_check_max_abs": model_check, "opt": opt, "warp_only_opt": warp_opt,
    "removed_events": removed, "seed": a.seed,
  }
  print("[mjlab] equivalence:", json.dumps(equiv, indent=1))
  np.savez_compressed(OUT / "getup_mjlab.npz", init_qpos=init_qpos, init_qvel=v0, pose=pose, origins=origins,
                      qpos=qlog, qvel=vlog, act=alog, obs_hist=np.array([obs_hist[k] for k, _ in TERMS]),
                      phys_dq=phys_dq_a, phys_dv=phys_dv_a, dt=env.step_dt)
  (OUT / "getup_equivalence.json").write_text(json.dumps(equiv, indent=1))
  import mujoco_warp
  (OUT / "getup_mjlab_meta.json").write_text(json.dumps({
    "mujoco": mujoco.__version__, "mujoco_warp": getattr(mujoco_warp, "__version__", "?"), "device": dev,
    "wall_s": time.time() - t0}, indent=1))
  print("[mjlab] wrote", OUT / "getup_mjlab.npz")


# ----------------------------------------------------------------------------------------------------------------
# Phase 2: native closed loop
# ----------------------------------------------------------------------------------------------------------------
def phase_native(a):
  import mujoco
  ref = np.load(OUT / "getup_mjlab.npz")
  init_qpos, init_qvel = ref["init_qpos"], ref["init_qvel"]
  n, T = init_qpos.shape[0], ref["qpos"].shape[0]
  nat = NativeG1(HERE / a.model)
  actor = CpuActor()
  fp = {f: np.asarray(getattr(nat.m, f), dtype=np.float64) for f in FP_FIELDS}
  fp_path = OUT / "getup_fingerprint.npz"
  model_diff = None
  if str(a.model).endswith(".mjb"):
    np.savez(fp_path, **fp)
  elif fp_path.exists():  # XML-compiled model vs the exported runtime model
    ref_fp = np.load(fp_path)
    model_diff = {f: (float(np.max(np.abs(fp[f] - ref_fp[f]))) if fp[f].shape == ref_fp[f].shape else
                      f"shape {fp[f].shape} vs {ref_fp[f].shape}") for f in FP_FIELDS}
    print(f"[native:{a.tag}] XML model vs mjb:", model_diff)
  qlog = np.zeros((T, n, nat.m.nq))
  vlog = np.zeros((T, n, nat.m.nv))
  alog = np.zeros((T, n, 29))
  t0 = time.time()
  t_pol = t_phys = 0.0
  for e in range(n):
    nat.set_state(init_qpos[e], init_qvel[e])
    last = np.zeros(29)
    for s in range(T):
      ta = time.perf_counter()
      act = actor(nat.obs(last))[0]
      tb = time.perf_counter()
      nat.step(act)
      t_pol += tb - ta
      t_phys += time.perf_counter() - tb
      last = act
      qlog[s, e], vlog[s, e], alog[s, e] = nat.d.qpos, nat.d.qvel, act
    if e % 16 == 0:
      print(f"[native:{a.tag}] episode {e}/{n} ({time.time() - t0:.0f}s)", flush=True)
  np.savez_compressed(OUT / f"getup_{a.tag}.npz", qpos=qlog, qvel=vlog, act=alog)
  meta = {"mujoco": mujoco.__version__, "model": str(a.model), "wall_s": time.time() - t0,
          "model_vs_mjb_max_abs": model_diff,
          "policy_ms_per_step": 1e3 * t_pol / (n * T), "physics_ms_per_policy_step": 1e3 * t_phys / (n * T)}
  (OUT / f"getup_{a.tag}_meta.json").write_text(json.dumps(meta, indent=1))
  print(f"[native:{a.tag}] done", meta)


# ----------------------------------------------------------------------------------------------------------------
# Phase 3: metrics, report, video
# ----------------------------------------------------------------------------------------------------------------
def kin(nat, qpos):
  """pelvis z and torso tilt (deg, torso z-axis vs world z) for qpos of shape (T, N, nq), via mj_kinematics."""
  T, n, _ = qpos.shape
  z = qpos[:, :, 2].copy()
  tilt = np.zeros((T, n))
  for t in range(T):
    for e in range(n):
      nat.d.qpos[:] = qpos[t, e]
      nat.mj.mj_kinematics(nat.m, nat.d)
      tilt[t, e] = np.degrees(np.arccos(np.clip(nat.d.xmat[nat.torso][8], -1.0, 1.0)))
  return z, tilt


def metrics(nat, qpos, qvel, pose, dt):
  z, tilt = kin(nat, qpos)
  T, n = z.shape
  ok = (z > 0.70) & (tilt < 15.0)
  hold = int(round(1.0 / dt))
  t_stand = np.full(n, np.nan)
  for e in range(n):
    run = 0
    for s in range(T):
      run = run + 1 if ok[s, e] else 0
      if run >= hold:
        # log index s is the state at time (s + 1) * dt; the run of `hold` OK samples ending at s starts at index
        # s - hold + 1, i.e. at time (s - hold + 2) * dt (= (s + 2) * dt - 1.0 for hold = 50, dt = 0.02)
        t_stand[e] = (s - hold + 2) * dt
        break
  peak = np.abs(qvel[:, :, 6:]).max(axis=(0, 2))
  end_ok = ok[-1]

  def block(mask):
    succ = ~np.isnan(t_stand[mask])
    return {"n": int(mask.sum()), "success_rate": float(succ.mean()),
            "time_to_stand_median_s": float(np.nanmedian(t_stand[mask])) if succ.any() else None,
            "final_torso_tilt_median_deg": float(np.median(tilt[-1, mask])),
            "final_pelvis_z_median_m": float(np.median(z[-1, mask])),
            "peak_joint_speed_median_rad_s": float(np.median(peak[mask])),
            "standing_at_end_frac": float(end_ok[mask].mean())}

  res = {"overall": block(np.ones(n, bool))}
  for k, nm in enumerate(POSE_NAMES):
    res[nm] = block(pose == k)
  per_ep = {"t_stand": t_stand.tolist(), "success": (~np.isnan(t_stand)).tolist(), "end_ok": end_ok.tolist()}
  return res, per_ep


def divergence(ref_q, q, dt):
  """Per-episode joint-qpos RMS and root-position distance vs the mjlab trajectory, statistics over episodes."""
  jr = np.sqrt(np.mean((ref_q[:, :, 7:] - q[:, :, 7:]) ** 2, axis=2))  # (T, N)
  rp = np.linalg.norm(ref_q[:, :, 0:3] - q[:, :, 0:3], axis=2)
  out = []
  for s in [0, 1, 2, 4, 9, 14, 19, 24, 29, 34, 39, 44, 49, 99, 149, 249, jr.shape[0] - 1]:
    if s < jr.shape[0]:
      out.append({"t_s": round((s + 1) * dt, 3), "joint_rms_median_rad": float(np.median(jr[s])),
                  "joint_rms_p90_rad": float(np.percentile(jr[s], 90)), "joint_rms_max_rad": float(jr[s].max()),
                  "root_pos_median_m": float(np.median(rp[s])), "root_pos_max_m": float(rp[s].max())})
  return out, jr


def render_video(nat, ref, nat_log, tag_label, path, seconds=6.0):
  import imageio.v2 as imageio
  import mujoco
  from PIL import Image, ImageDraw, ImageFont
  W = H = 480
  r = mujoco.Renderer(nat.m, H, W)
  cam = mujoco.MjvCamera()
  cam.type = mujoco.mjtCamera.mjCAMERA_FREE
  cam.distance, cam.azimuth, cam.elevation = 2.8, 135.0, -12.0
  try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 17)
  except OSError:
    font = ImageFont.load_default()
  dt = float(ref["dt"])
  pose = ref["pose"]
  T = min(int(round(seconds / dt)), ref["qpos"].shape[0])
  frames = []
  for k, nm in enumerate(POSE_NAMES):
    e = int(np.where(pose == k)[0][0])
    # ONE fixed camera per episode for both halves (lookat = mean mjlab root xy over the clip), so root drift and the
    # root offset between the two simulators are visible; the first frame is the shared reset state (t = 0)
    look = [float(ref["qpos"][:T, e, 0].mean()), float(ref["qpos"][:T, e, 1].mean()), 0.45]
    for s in [-1] + list(range(1, T, 2)):
      qm = ref["init_qpos"][e] if s < 0 else ref["qpos"][s, e]
      qn = ref["init_qpos"][e] if s < 0 else nat_log["qpos"][s, e]
      t = (s + 1) * dt
      imgs = []
      for side, q in (("mjlab (mujoco_warp, GPU)", qm), (tag_label, qn)):
        nat.d.qpos[:] = q
        mujoco.mj_forward(nat.m, nat.d)
        cam.lookat[:] = look
        r.update_scene(nat.d, cam)
        im = Image.fromarray(r.render())
        dr = ImageDraw.Draw(im)
        dr.rectangle([0, 0, W, 72], fill=(0, 0, 0))
        dr.text((8, 4), side, fill=(255, 255, 255), font=font)
        dr.text((8, 26), f"{nm}  ep {e}  t={t:4.2f}s  z={q[2]:.2f}m", fill=(255, 220, 120), font=font)
        if q is qn:
          dr.text((8, 48), f"root xy offset vs mjlab: {100 * np.linalg.norm(qn[0:2] - qm[0:2]):.1f} cm",
                  fill=(160, 220, 255), font=font)
        else:
          dr.text((8, 48), "fixed camera, same for both halves", fill=(160, 220, 255), font=font)
        imgs.append(np.asarray(im))
      frames.append(np.concatenate([imgs[0], np.full((H, 4, 3), 255, np.uint8), imgs[1]], axis=1))
  path.parent.mkdir(parents=True, exist_ok=True)
  imageio.mimsave(path, frames, fps=int(round(0.5 / dt)), macro_block_size=1)
  r.close()


def phase_report(a):
  import mujoco
  ref = np.load(OUT / "getup_mjlab.npz")
  dt = float(ref["dt"])
  pose = ref["pose"]
  nat = NativeG1()
  equiv = json.loads((OUT / "getup_equivalence.json").read_text())
  sims = {"mjlab": {"qpos": ref["qpos"], "qvel": ref["qvel"]}}
  metas = {"mjlab": json.loads((OUT / "getup_mjlab_meta.json").read_text())}
  for tag in ("native", "native_xml35", "native_v316"):
    p = OUT / f"getup_{tag}.npz"
    if p.exists():
      sims[tag] = dict(np.load(p))
      metas[tag] = json.loads((OUT / f"getup_{tag}_meta.json").read_text())
  res = {"policy": str(POLICY.relative_to(ROOT)), "task": TASK, "n_initial_states": int(len(pose)),
         "episode_s": round(ref["qpos"].shape[0] * dt, 3), "dt": dt,
         "pose_counts": {nm: int((pose == k).sum()) for k, nm in enumerate(POSE_NAMES)},
         "success_definition": "pelvis z > 0.70 m and torso tilt < 15 deg in 50 consecutive policy-step samples "
                               "(0.02 s apart, i.e. held for 1 s); time-to-stand = time of the FIRST sample of the "
                               "first such run (state at t = (index + 1) * dt, t = 0 is the reset state)","equivalence": equiv, "sims": {}, "divergence_vs_mjlab": {},
         "per_episode": {}, "meta": metas}
  for tag, lg in sims.items():
    m, pe = metrics(nat, lg["qpos"], lg["qvel"], pose, dt)
    res["sims"][tag] = m
    res["per_episode"][tag] = pe
    if tag != "mjlab":
      res["divergence_vs_mjlab"][tag], _ = divergence(ref["qpos"], lg["qpos"], dt)
  # native-vs-native: XML vs mjb in the same MuJoCo (export effect), MuJoCo 3.16 vs 3.5 on the same XML (version)
  res["divergence_native_pairs"] = {}
  for x, y in (("native_xml35", "native"), ("native_v316", "native_xml35")):
    if x in sims and y in sims:
      res["divergence_native_pairs"][f"{x} vs {y}"], _ = divergence(sims[y]["qpos"], sims[x]["qpos"], dt)
  res["success_agreement_vs_mjlab"] = {}
  a_ = np.array(res["per_episode"]["mjlab"]["success"])
  for tag in sims:
    if tag != "mjlab":
      b_ = np.array(res["per_episode"][tag]["success"])
      res["success_agreement_vs_mjlab"][tag] = {"both": int((a_ & b_).sum()), "mjlab_only": int((a_ & ~b_).sum()),
                                                f"{tag}_only": int((~a_ & b_).sum()), "neither": int((~a_ & ~b_).sum())}
  dp = OUT / "getup_diag.json"
  if dp.exists():
    res["physics_difference_diagnostic"] = json.loads(dp.read_text())
  sp = OUT / "getup_satdiag.json"
  if sp.exists():
    res["actuator_saturation_diagnostic"] = json.loads(sp.read_text())
  sp = OUT / "getup_satnames.json"  # fix_getup_satnames.py
  if sp.exists():
    res["saturation_by_phase_native"] = json.loads(sp.read_text())
  (HERE / "results_getup.json").write_text(json.dumps(res, indent=1))
  print(json.dumps({k: res[k] for k in ("sims", "divergence_vs_mjlab")}, indent=1))
  if "native" in sims and not a.no_video:
    vp = VIDEO_DIR / "getup_side_by_side.mp4"
    render_video(nat, ref, sims["native"], f"native MuJoCo {mujoco.__version__} (CPU)", vp)
    res["video"] = str(vp.relative_to(ROOT))
    print("video:", vp)
  (HERE / "results_getup.json").write_text(json.dumps(res, indent=1))
  write_md(res)


def sat_md(sat):
  """Markdown for out/getup_satdiag.json (diag_getup_sat.py)."""
  ap = sat["actuator_params"]
  L = ["", "### (2) Saturated actuators x implicitfast (`diag_getup_sat.py`)", "",
       f"Setup: {sat['what']}.", "",
       f"Source: {sat['warp_source']}. Actuators: kp {ap['kp_min_max'][0]:.0f}-{ap['kp_min_max'][1]:.0f}, kv "
       f"{ap['kv_min_max'][0]:.2f}-{ap['kv_min_max'][1]:.2f}, joint damping {ap['dof_damping_actuated_min_max'][0]:.2g}-"
       f"{ap['dof_damping_actuated_min_max'][1]:.2g}, |force range| {ap['forcerange_abs_min_max'][0]:.0f}-"
       f"{ap['forcerange_abs_min_max'][1]:.0f} Nm, {ap['n_forcelimited']} of 29 force-limited.", ""]
  qc = sat["qderiv_diag_check_pushed_state"]
  if "skipped" not in qc:
    L += ["Diagonal of the velocity derivative qDeriv at each actuated dof, pushed state (push levels > 0); native = "
          "`d.qDeriv` after `mj_step`, warp = `derivative.deriv_smooth_vel` on the same state; fraction of entries "
          "equal (rel. 1e-3) to -(damping + kv) or to -damping:", "",
          "| actuator state | n | native = -(damping+kv) | native = -damping | warp = -(damping+kv) | warp = -damping | "
          "max abs native - warp |", "|---|---|---|---|---|---|---|"]
    for k, lab in (("unsat", "not saturated"), ("sat", "force-saturated")):
      r = qc[k]
      if r["n"]:
        L.append(f"| {lab} | {r['n']} | {r['native_matches_with_kv_frac']:.0%} | {r['native_matches_without_kv_frac']:.0%}"
                 f" | {r['warp_matches_with_kv_frac']:.0%} | {r['warp_matches_without_kv_frac']:.0%} | "
                 f"{r['max_abs_native_minus_warp']:.2f} |")
    L.append("")
  L += ["Single 5 ms substep, same state + warm start + ctrl; |qvel diff| (rad/s) median / max over envs, and the "
        "fraction of envs whose worst dof is driven by a saturated actuator (push level 1.0 envs; reset state: all "
        "envs). 'warp-style derivative' changes ONLY the native side: for saturated actuators the force/ctrl limits "
        "are lifted and ctrl is shifted so that the applied force equals the clamped force, which keeps -kv in "
        f"qDeriv as mujoco_warp does (sanity: with the Euler integrator this variant equals nominal native to "
        f"{sat['warpstyle_vs_nominal_native_under_euler_max_dqvel']:.1e}).", ""]
  ss = sat["single_substep"]
  snames = list(next(iter(ss.values())).keys())
  L += ["| variant | " + " | ".join(snames) + " |", "|---|" + "---|" * len(snames)]
  for var, by_state in ss.items():
    cells = []
    for sn in snames:
      g = by_state[sn].get("push level 1.0", by_state[sn].get("all envs"))
      cells.append(f"{g['dqvel_median']:.1e} / {g['dqvel_max']:.1e} ({g['worst_dof_actuator_saturated_frac']:.0%})")
    L.append(f"| {var} | " + " | ".join(cells) + " |")
  cl = sat["closed_loop_after_push"]
  sims = ("mjlab", "native", "native_warpstyle_deriv")
  L += ["", "Closed loop after the push (both simulators start from the identical pushed state at t = 4 s and run to "
        f"10 s). {sat['outcome_definitions']}. Joint RMS / root distance are native vs mjlab:", "",
        "| push level | n | recovered mjlab / native / native warp-style | fell mjlab / native / warp-style | "
        "joint RMS median (max) +0.1 s, native | +1 s | +6 s | root max +6 s | joint RMS median (max) +1 s, "
        "warp-style | +6 s | root max +6 s, warp-style |", "|---|---|---|---|---|---|---|---|---|---|---|"]

  def at(rows, t):
    return min(rows, key=lambda r: abs(r["t_s"] - t))
  for lv, r in cl.items():
    dn, dw = r["divergence_native_vs_mjlab"], r["divergence_native_warpstyle_deriv_vs_mjlab"]
    L.append(f"| {lv} | {r['n']} | " + " / ".join(f"{r[s]['recovered']:.0%}" for s in sims) + " | "
             + " / ".join(f"{r[s]['fell']:.0%}" for s in sims) + " | "
             + " | ".join(f"{at(dn, t)['joint_rms_median_rad']:.3f} ({at(dn, t)['joint_rms_max_rad']:.3f})"
                          for t in (0.1, 1.0, 6.0))
             + f" | {at(dn, 6.0)['root_pos_max_m']:.2f} m | "
             + " | ".join(f"{at(dw, t)['joint_rms_median_rad']:.3f} ({at(dw, t)['joint_rms_max_rad']:.3f})"
                          for t in (1.0, 6.0))
             + f" | {at(dw, 6.0)['root_pos_max_m']:.2f} m |")
  for lv, r in cl.items():
    L.append(f"\nPer-env recovered agreement at push level {lv}: mjlab vs native {r['recovered_agreement_mjlab_vs_native']}; "
             f"mjlab vs native warp-style {r['recovered_agreement_mjlab_vs_native_warpstyle_deriv']}")
  worst = {lv: max(x["root_pos_max_m"] for x in r["divergence_native_vs_mjlab"]) for lv, r in cl.items()}
  worst_w = {lv: max(x["root_pos_max_m"] for x in r["divergence_native_warpstyle_deriv_vs_mjlab"]) for lv, r in cl.items()}
  L += ["", "Reading: after a push the nominal native trajectories leave the mjlab ones (largest root distance over the "
        "6 s, by push level: " + ", ".join(f"{lv}: {v:.2f} m" for lv, v in worst.items()) + "), while the native run "
        "with the warp-style derivative stays close (" + ", ".join(f"{lv}: {v:.2f} m" for lv, v in worst_w.items())
        + "). Outcome rates still agree within the counts above; per-episode outcomes can differ once the push is "
        "strong enough to make episodes marginal."]
  gd = sat["getup_phase_divergence_vs_mjlab"]
  sc = sat["saturation_counts"]
  L += ["", "Nominal get-up (no push, 32 envs, first 4 s): native vs mjlab divergence with the nominal and with the "
        "warp-style derivative, joint RMS median (max) rad:", "",
        "| t (s) | " + " | ".join(str(r["t_s"]) for r in gd["native"]) + " |", "|---|" + "---|" * len(gd["native"])]
  for tag in gd:
    L.append(f"| {tag} | " + " | ".join(f"{r['joint_rms_median_rad']:.3f} ({r['joint_rms_max_rad']:.3f})"
                                        for r in gd[tag]) + " |")
  L += ["", f"Saturation counts (native, warp-style run): get-up phase {sc['getup_phase_saturated_actuator_substeps_per_env_mean']:.0f}"
        f" saturated actuator-substeps per env out of {sc['getup_phase_actuator_substeps_per_env']}; after the push "
        f"(6 s), per env by push level: {', '.join(f'{k}: {v:.0f}' for k, v in sc['after_push_saturated_actuator_substeps_per_env'].items())}."]
  return L


def write_md(res):
  eq = res["equivalence"]
  L = ["# Sim2sim: get-up policy (getup_auto_r08) - mjlab vs native MuJoCo", "",
       f"Policy `{res['policy']}`, task `{res['task']}`, {res['n_initial_states']} initial states from the mjlab reset "
       f"({', '.join(f'{k} {v}' for k, v in res['pose_counts'].items())}), {res['episode_s']} s episodes, "
       f"policy dt {res['dt']} s (4 x 5 ms physics). No randomisation in either simulator (startup events "
       f"{', '.join(eq['removed_events'])} removed from the mjlab play env; the native side uses the exported nominal "
       f"model). Generated by `sim2sim/native_getup.py`; raw numbers in `results_getup.json`.", "",
       "## Equivalence test (mjlab state copied into native MjData)", "",
       f"{eq['obs_compared_states']} states ({eq['n_envs']} envs x ({eq['n_steps']} steps + reset)).", "",
       "| obs term | max abs diff | < 1e-4 | what the comparison actually tests |", "|---|---|---|---|"]
  how = eq.get("obs_term_what_is_tested", {})
  for k, v in eq["obs_max_abs_diff"].items():
    L.append(f"| {k} | {v:.2e} | {'yes' if v < 1e-4 else 'NO'} | {how.get(k, '')} |")
  L += ["", f"Max |mjlab twist command| over all compared states: {eq['mjlab_command_max_abs']:.1e}."]
  es, ss = eq["env_step_4_substeps"], eq["single_substep"]
  L += ["", f"- CPU actor re-implementation vs rsl_rl runner policy (same obs): max |diff| "
        f"{eq['actor_cpu_vs_runner_max_abs_diff']:.2e}",
        f"- native action->ctrl vs mjlab ctrl: max |diff| {eq['ctrl_native_vs_mjlab_max_abs_diff']:.2e}",
        f"- one physics substep (5 ms), same state + qacc_warmstart + ctrl, {ss['qpos']['n']} cases: |dqpos| median "
        f"{ss['qpos']['median']:.2e} / p99 {ss['qpos']['p99']:.2e} / max {ss['qpos']['max']:.2e}; |dqvel| median "
        f"{ss['qvel']['median']:.2e} / p99 {ss['qvel']['p99']:.2e} / max {ss['qvel']['max']:.2e}",
        f"- one env step (4 substeps), {es['qpos']['n']} cases: |dqpos| median {es['qpos']['median']:.2e} / p99 "
        f"{es['qpos']['p99']:.2e} / max {es['qpos']['max']:.2e}; |dqvel| median {es['qvel']['median']:.2e} / p99 "
        f"{es['qvel']['p99']:.2e} / max {es['qvel']['max']:.2e}", "",
        "## Closed loop, same initial states", ""]
  tags = list(res["sims"])
  L += ["| metric | " + " | ".join(tags) + " |", "|---|" + "---|" * len(tags)]
  keys = [("success_rate", "success rate", "{:.0%}"), ("time_to_stand_median_s", "time-to-stand median (s)", "{:.2f}"),
          ("final_torso_tilt_median_deg", "final torso tilt median (deg)", "{:.1f}"),
          ("final_pelvis_z_median_m", "final pelvis z median (m)", "{:.3f}"),
          ("peak_joint_speed_median_rad_s", "peak joint speed median (rad/s)", "{:.1f}"),
          ("standing_at_end_frac", "standing at the end", "{:.0%}")]
  for grp in ["overall"] + POSE_NAMES:
    L.append(f"| **{grp}** (n={res['sims'][tags[0]][grp]['n']}) |" + " |" * len(tags))
    for k, lab, fmt in keys:
      vals = [res["sims"][t][grp][k] for t in tags]
      L.append(f"| {lab} | " + " | ".join("-" if v is None else fmt.format(v) for v in vals) + " |")
  for tag, agr in res.get("success_agreement_vs_mjlab", {}).items():
    L.append(f"\nPer-episode success agreement, mjlab vs {tag}: {agr}")
  L += ["", "| simulator | MuJoCo | model | wall time | policy ms / step | physics ms / policy step |", "|---|---|---|---|---|---|"]
  for tag, mt in res["meta"].items():
    if tag == "mjlab":
      L.append(f"| mjlab | {mt['mujoco']} + mujoco_warp {mt['mujoco_warp']} ({mt['device']}, {res['n_initial_states']} "
               f"worlds batched, incl. per-step equivalence checks) | runtime | {mt['wall_s']:.0f} s | - | - |")
    else:
      L.append(f"| {tag} | {mt['mujoco']} (CPU, 1 thread) | `{mt['model']}` | {mt['wall_s']:.0f} s | "
               f"{mt['policy_ms_per_step']:.3f} | {mt['physics_ms_per_policy_step']:.3f} |")
      if mt.get("model_vs_mjb_max_abs"):
        bad = {k: v for k, v in mt["model_vs_mjb_max_abs"].items() if not isinstance(v, float) or v > 1e-6}
        L.append(f"|  | XML model vs exported mjb: {len(FP_FIELDS)} arrays compared, differences > 1e-6: "
                 f"{bad if bad else 'none'} | | | | |")
  dg = res.get("physics_difference_diagnostic")
  sat = res.get("actuator_saturation_diagnostic")
  if dg or sat:
    L += ["", "## Where the physics differences come from", "",
          "Two separate mechanisms make a single mujoco_warp substep differ from a C-MuJoCo substep from the same "
          "state. (1) Contacts: at contact-rich lying states some contacts get a different pyramidal tangent frame "
          "(below; switching both sims to the elliptic cone removes most of it). (2) Force-saturated position "
          "actuators under `implicitfast`: mujoco_warp keeps the actuator damping term (-kv) in the implicit velocity "
          "derivative even when the actuator force is clamped by its force range, C MuJoCo does not (measured below: "
          "qDeriv diagonal, and a native run that keeps -kv for saturated actuators reproduces mujoco_warp's substep "
          "to ~1e-4 rad/s). The difference scales with how hard the saturated joints accelerate, so (2) dominates "
          "after pushes / impacts / large tracking errors, while in the quiet parts of the nominal get-up both "
          "mechanisms are small enough that the closed-loop numbers above agree."]
    sn = res.get("saturation_by_phase_native")
    if sn:
      L += ["", "Saturated actuators in the nominal native get-up (64 envs, evaluated at the start of each policy step), "
            "fraction of actuator-steps and the most often saturated actuators:", "",
            "| phase | saturated fraction | most often saturated (fraction of steps) |", "|---|---|---|"]
      for ph, r in sn.items():
        if isinstance(r, dict):
          L.append(f"| {ph} | {r['saturated_actuator_frac_of_actuator_steps']:.1%} | "
                   + ", ".join(f"{k} {v:.0%}" for k, v in r["per_actuator_frac_top"].items()) + " |")
      L += ["", "Both ankle-roll actuators (force range 50 Nm) stay at their force limit for the whole standing phase, so "
            "any perturbation while standing immediately goes through saturated actuators (mechanism (2))."]
  if dg:
    L += ["", "### (1) Contact frames (`diag_getup.py`, 8 envs, single 5 ms substep)", "",
          "Max |qvel diff| over the 8 envs, same state + warm start + ctrl in both simulators:", "",
          "| variant (applied to both sims) | step 0 | step 1 | step 10 | step 50 |", "|---|---|---|---|---|"]
    for name, by_step in dg["variants"].items():
      if isinstance(by_step, dict):
        L.append(f"| {name} | " + " | ".join(f"{max(by_step[s]):.1e}" for s in ("0", "1", "10", "50")) + " |")
    L += ["", f"Contacts with a different tangent frame at step 0 (per env, mismatched/total): "
          f"{dg['contact_tangent_frame_mismatch_step0']}. Native self-sensitivity to float32-sized state noise: "
          f"max |dqvel| {dg['native_self_sensitivity_max_dqvel']:.1e} (the problem is well conditioned, so the large "
          "differences are not float32 round-off)."]
  if sat:
    L += sat_md(sat)
  for tag, dv in res["divergence_vs_mjlab"].items():
    L += ["", f"## Trajectory divergence, {tag} vs mjlab (over episodes)", "",
          "| t (s) | joint qpos RMS median (rad) | p90 | max | root pos median (m) | max |", "|---|---|---|---|---|---|"]
    for r in dv:
      L.append(f"| {r['t_s']} | {r['joint_rms_median_rad']:.2e} | {r['joint_rms_p90_rad']:.2e} | "
               f"{r['joint_rms_max_rad']:.2e} | {r['root_pos_median_m']:.2e} | {r['root_pos_max_m']:.2e} |")
  if res.get("divergence_native_pairs"):
    L += ["", "## Native vs native (export and version effects)", "",
          "| pair | t (s) | joint qpos RMS median (rad) | max | root pos max (m) |", "|---|---|---|---|---|"]
    for pair, dv in res["divergence_native_pairs"].items():
      for r in dv:
        if r["t_s"] in (0.02, 0.1, 1.0, 10.0):
          L.append(f"| {pair} | {r['t_s']} | {r['joint_rms_median_rad']:.2e} | {r['joint_rms_max_rad']:.2e} | "
                   f"{r['root_pos_max_m']:.2e} |")
  if "video" in res:
    L += ["", f"Video: `{res['video']}`. Left: the logged mjlab (mujoco_warp) qpos, kinematically replayed with the native "
          "model (it is the mjlab trajectory, only drawn by the native renderer). Right: the native closed-loop qpos "
          "(`out/getup_native.npz`). First 6 s of one episode per pose, starting with the shared reset state at t = 0, "
          "then every 2nd policy step (0.04 s). Both halves use the same fixed camera per episode, so root drift and "
          "the root offset between the simulators are visible (the native half prints the root xy offset)."]
  L += ["", "Pose names: side_roll+90 / side_roll-90 = roll +-90 deg about the body x axis (lying on a side).", ""]
  (HERE / "results_getup.md").write_text("\n".join(L))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("phase", choices=["mjlab", "native", "report"])
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--steps", type=int, default=500)
  ap.add_argument("--seed", type=int, default=0)
  ap.add_argument("--model", default="models/getup.mjb")
  ap.add_argument("--tag", default="native")
  ap.add_argument("--no_video", action="store_true")
  args = ap.parse_args()
  {"mjlab": phase_mjlab, "native": phase_native, "report": phase_report}[args.phase](args)
