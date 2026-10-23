"""Adversarial verifier for the dance sim2sim (native_dance.py). Writes only verify_dance_<clip>.json.

Part A (equivalence on NEW states): seed 4242, start frames not used by native_dance.py, three scenarios
  late   : plain policy rollout, every step checked (incl. late in the clip)
  push   : every 20 steps a random root-velocity push + joint pos/vel perturbation written into mjlab's warp data;
           the obs at the perturbed state is checked directly (sim.forward + observation_manager.compute) and the
           perturbed state is then stepped in both sims
  noise  : policy action + N(0, 0.3) noise (drives the robot off-distribution / into falls)
  Per step: obs per-term max |diff| for (i) native_dance.NativeG1.obs_terms (code under test) and (ii) an
  independent obs implementation written here (quaternion math, site velocity via mj_objectVelocity, mjlab's own
  default_joint_pos / joint order), policy action diff (native_dance.Policy vs mjlab runner inference policy),
  ctrl target diff, one policy step (4 substeps) qpos/qvel diff from identical pre-state + warm start.
Part B (closed loop, 3 starts): mjlab rollout vs native_dance.native_rollout, metrics via native_dance.run_metrics,
  plus mjlab's own MotionCommand metrics recorded online to check the metric definitions.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import native_dance as nd  # noqa: E402  (code under test)

SEED = 4242


def quat_to_mat(q):
  w, x, y, z = q / np.linalg.norm(q)
  return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - w * z), 2 * (x * z + w * y)],
                   [2 * (x * y + w * z), 1 - 2 * (x * x + z * z), 2 * (y * z - w * x)],
                   [2 * (x * z - w * y), 2 * (y * z + w * x), 1 - 2 * (x * x + y * y)]])


def qmul(a, b):
  w1, x1, y1, z1 = a
  w2, x2, y2, z2 = b
  return np.array([w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2, w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                   w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2, w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2])


class IndepObs:
  """Independent re-implementation of the 154-d actor obs from the mjlab source (not from native_dance)."""

  def __init__(self, m, robot, mot_npz, cmd):
    self.m = m
    J = mujoco.mjtObj.mjOBJ_JOINT
    self.jn = list(robot.joint_names)
    self.qadr = np.array([m.jnt_qposadr[mujoco.mj_name2id(m, J, "robot/" + n)] for n in self.jn])
    self.dadr = np.array([m.jnt_dofadr[mujoco.mj_name2id(m, J, "robot/" + n)] for n in self.jn])
    self.default = robot.data.default_joint_pos[0].double().cpu().numpy()
    self.torso = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "robot/torso_link")
    sid = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_SENSOR, "robot/imu_ang_vel")
    assert m.sensor_type[sid] == mujoco.mjtSensor.mjSENS_GYRO
    self.site = int(m.sensor_objid[sid])
    z = np.load(mot_npz)
    f32 = lambda k: np.asarray(z[k], dtype=np.float32).astype(np.float64)
    self.jp, self.jv, self.bq = f32("joint_pos"), f32("joint_vel"), f32("body_quat_w")
    # anchor index inside the npz body axis: mjlab indexes npz bodies by robot.find_bodies(body_names)
    self.anchor_npz = int(cmd.body_indexes[cmd.motion_anchor_body_index].item())

  def terms(self, d, t, last_a):
    q_rob = d.xquat[self.torso].copy()
    q_ref = self.bq[t, self.anchor_npz]
    q_rel = qmul(np.array([q_rob[0], -q_rob[1], -q_rob[2], -q_rob[3]]) / np.dot(q_rob, q_rob), q_ref)
    R = quat_to_mat(q_rel)
    v6 = np.zeros(6)
    mujoco.mj_objectVelocity(self.m, d, mujoco.mjtObj.mjOBJ_SITE, self.site, v6, 1)  # local frame, [rot, lin]
    return [np.concatenate([self.jp[t], self.jv[t]]), R[:, :2].reshape(-1), v6[:3].copy(),
            d.qpos[self.qadr] - self.default, d.qvel[self.dadr].copy(), np.asarray(last_a, float)]


def stat(x):
  x = np.asarray(x, float)
  if x.size == 0:
    return None
  return dict(n=int(x.size), median=float(np.median(x)), p99=float(np.percentile(x, 99)), max=float(x.max()),
              frac_gt_1e_3=float(np.mean(x > 1e-3)), frac_gt_1e_1=float(np.mean(x > 0.1)))


def main(a):
  sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
  from dataclasses import asdict

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  tag, _ = nd.CLIPS[a.clip]
  pdir = nd.ROOT / "policies" / tag
  info = json.loads((HERE / "models" / "dance_info.json").read_text())
  dev = "cuda:0"
  cfg = load_env_cfg(nd.TASK, play=True)
  cfg.scene.num_envs = 1
  mc = cfg.commands["motion"]
  mc.motion_file = str(pdir / "reference_motion.npz")
  mc.pose_range, mc.velocity_range, mc.joint_position_range = {}, {}, (0.0, 0.0)
  for k in ("base_com", "encoder_bias", "foot_friction", "push_robot"):
    cfg.events.pop(k, None)
  for k in [k for k in list(cfg.terminations) if k != "time_out"]:
    cfg.terminations.pop(k)
  assert cfg.observations["actor"].enable_corruption is False
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent_cfg = load_rl_cfg(nd.TASK)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(nd.TASK) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(str(pdir / "policy.pt"), load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  cmd = env.command_manager.get_term("motion")
  robot = env.scene["robot"]
  start = [0]
  cmd.cfg.sampling_mode = "uniform"
  cmd._uniform_sampling = lambda env_ids: cmd.time_steps.__setitem__(env_ids, start[0])
  origin = env.scene.env_origins[0].double().cpu().numpy()
  npy = lambda x: torch.as_tensor(x).detach().double().cpu().numpy()
  tt = lambda x: torch.as_tensor(x, dtype=env.sim.data.qpos.dtype, device=env.sim.data.qpos.device)

  # actor obs layout as mjlab reports it (names + dims + order)
  om = env.observation_manager
  layout = [(n, list(om._group_obs_term_dim["actor"][i])) for i, n in enumerate(om._group_obs_term_names["actor"])]
  assert [n for n, _ in layout] == list(nd.TERMS) and [d[0] for _, d in layout] == list(nd.DIMS), layout
  act_term = env.action_manager._terms["joint_pos"]

  m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
  g = nd.NativeG1(m, info)
  pol = nd.Policy(pdir / "policy.pt")
  mot = nd.Motion(pdir / "reference_motion.npz")
  ind = IndepObs(m, robot, pdir / "reference_motion.npz", cmd)
  T, dt = mot.T, float(info["step_dt"])
  # static facts: joint order, scale, offset, default pos vs live mjlab objects
  facts = dict(
    joint_order_equal=list(robot.joint_names) == list(g.jnames),
    action_target_names_equal=list(act_term.target_names) == list(g.jnames),
    scale_max_abs=float(np.abs(npy(act_term.scale).reshape(-1)[-29:] - g.scale).max()),
    offset_max_abs=float(np.abs(npy(act_term.offset).reshape(-1)[-29:] - g.default).max()),
    default_pos_max_abs=float(np.abs(npy(robot.data.default_joint_pos[0]) - g.default).max()),
    soft_limits_max_abs=float(max(np.abs(npy(robot.data.soft_joint_pos_limits[0])[:, 0] - g.soft_lo).max(),
                                  np.abs(npy(robot.data.soft_joint_pos_limits[0])[:, 1] - g.soft_hi).max())),
    decimation=[int(cfg.decimation), g.decim], timestep=[float(env.sim.mj_model.opt.timestep), float(m.opt.timestep)],
    anchor_npz_index=[ind.anchor_npz, g.mot_idx[nd.ANCHOR]], actor_layout=layout,
    clip_actions=agent_cfg.clip_actions, env_origin=origin.tolist())
  print("[facts]", json.dumps(facts), flush=True)

  def mj_state():
    q, v = npy(env.sim.data.qpos[0]).copy(), npy(env.sim.data.qvel[0]).copy()
    q[:3] -= origin
    return q, v, npy(env.sim.data.qacc_warmstart[0]).copy()

  de = mujoco.MjData(m)
  rng = np.random.default_rng(SEED + (0 if a.clip == "sss" else 1))
  used = set(json.loads((HERE / f"results_dance_{a.clip}.json").read_text(encoding="utf-8"))["starts"])
  pool = np.array([x for x in range(1, T - 80) if x not in used])
  starts_eq = sorted(int(x) for x in rng.choice(pool, 3, replace=False))

  def obs_cmp(acc, t, last_a, tag_):
    q, v, _ = mj_state()
    g.set_state(de, q, v)
    ref = npy(env.obs_buf["actor"][0]) if tag_ == "post" else acc["_pre_ref"]
    for impl, terms in (("native_dance", g.obs_terms(de, mot, t, last_a)), ("independent", ind.terms(de, t, last_a))):
      i = 0
      for name, dim, x in zip(nd.TERMS, nd.DIMS, terms):
        k = f"{impl}/{name}"
        acc["obs"][k] = max(acc["obs"].get(k, 0.0), float(np.abs(x - ref[i:i + dim]).max()))
        i += dim

  results = {}
  for scen in ("late", "push", "noise"):
    acc = dict(obs={}, obs_perturbed={}, act=[], ctrl=[], sq=[], sv=[], n=0, pushes=0, falls=0, worst=None)
    for f in starts_eq:
      start[0] = f
      env.reset()
      obs = venv.get_observations()
      assert int(cmd.time_steps[0]) == f
      nsteps = T - 1 - f
      fell = False
      for k in range(nsteps):
        if scen == "push" and k > 0 and k % 20 == 0:
          q = env.sim.data.qpos[0].clone()
          v = env.sim.data.qvel[0].clone()
          v[g.rv:g.rv + 3] += tt(rng.uniform([-0.5, -0.5, -0.2], [0.5, 0.5, 0.2]))
          v[g.rv + 3:g.rv + 6] += tt(rng.uniform(-0.5, 0.5, 3))
          q[g.qadr] += tt(rng.uniform(-0.15, 0.15, 29))
          v[g.dadr] += tt(rng.uniform(-1.0, 1.0, 29))
          env.sim.data.qpos[0] = q
          env.sim.data.qvel[0] = v
          env.sim.forward()
          env.sim.sense()
          # update_history=True forces a recompute (compute(False) returns the cached buffer); the actor group
          # has no history/delay terms, so nothing else changes
          env.obs_buf = env.observation_manager.compute(update_history=True)
          obs = venv.get_observations()
          # direct obs check at the perturbed state (time step not advanced)
          q0, v0, _ = mj_state()
          g.set_state(de, q0, v0)
          ref = npy(obs["actor"][0])
          la = npy(env.action_manager.action[0])
          for impl, terms in (("native_dance", g.obs_terms(de, mot, int(cmd.time_steps[0]), la)),
                              ("independent", ind.terms(de, int(cmd.time_steps[0]), la))):
            i = 0
            for name, dim, x in zip(nd.TERMS, nd.DIMS, terms):
              kk = f"{impl}/{name}"
              acc["obs_perturbed"][kk] = max(acc["obs_perturbed"].get(kk, 0.0), float(np.abs(x - ref[i:i + dim]).max()))
              i += dim
          acc["pushes"] += 1
        pq, pv, pw = mj_state()
        with torch.no_grad():
          act = policy(obs)
        acc["act"].append(float(np.abs(pol(npy(obs["actor"][0])) - npy(act[0])).max()))
        if scen == "noise":
          act = act + torch.as_tensor(rng.normal(0, 0.3, act.shape), dtype=act.dtype, device=act.device)
        a_np = npy(act[0])
        obs, _, _, _ = venv.step(act)
        q1, v1, _ = mj_state()
        g.set_state(de, pq, pv, pw)
        g.step(de, a_np)
        acc["ctrl"].append(float(np.abs(de.ctrl - npy(env.sim.data.ctrl[0])).max()))
        acc["sq"].append(float(np.abs(de.qpos - q1).max()))
        acc["sv"].append(float(np.abs(de.qvel - v1).max()))
        if acc["worst"] is None or acc["sv"][-1] > acc["worst"]["qvel"]:
          acc["worst"] = dict(start=f, step=k, qvel=acc["sv"][-1], qpos=acc["sq"][-1], native_ncon=int(de.ncon),
                              dof=int(np.argmax(np.abs(de.qvel - v1))))
        t_now = int(cmd.time_steps[0])
        assert t_now == f + k + 1, (t_now, f, k)
        obs_cmp(acc, t_now, npy(env.action_manager.action[0]), "post")
        acc["n"] += 1
        g.set_state(de, q1, v1)
        if g.fell(de) and not fell:
          fell = True
          acc["falls"] += 1
    results[scen] = dict(starts=starts_eq, steps=acc["n"], pushes=acc["pushes"], runs_that_fell=acc["falls"],
                         obs_term_max_abs=acc["obs"], obs_at_perturbed_state_max_abs=acc["obs_perturbed"] or None,
                         policy_action_max_abs=stat(acc["act"]), ctrl_max_abs=stat(acc["ctrl"]),
                         step4_qpos_max_abs=stat(acc["sq"]), step4_qvel_max_abs=stat(acc["sv"]), worst=acc["worst"])
    print(f"[eq:{scen}]", json.dumps(results[scen]), flush=True)

  # ---------------- Part B: closed loop on 3 starts (2 from the report + 1 new)
  rep = json.loads((HERE / f"results_dance_{a.clip}.json").read_text(encoding="utf-8"))
  rs = rep["starts"]
  starts_cl = [0, rs[4], starts_eq[1]]
  cl = []
  for f in starts_cl:
    start[0] = f
    env.reset()
    obs = venv.get_observations()
    traj_m, onl = [mj_state()[0]], dict(error_body_pos=[], error_anchor_rot=[], error_joint_pos=[])
    for k in range(T - 1 - f):
      with torch.no_grad():
        obs, _, _, _ = venv.step(policy(obs))
      traj_m.append(mj_state()[0])
      # mjlab metrics are updated in command.compute() BEFORE time_steps += 1, i.e. robot state after step k+1
      # vs reference frame f+k (and body_pos_relative_w built from the robot anchor after step k)
      for kk in onl:
        onl[kk].append(float(cmd.metrics[kk][0]))
      g.set_state(de, traj_m[-1], np.zeros(m.nv))
      if g.fell(de):
        break
    traj_m = np.array(traj_m)
    t0 = time.perf_counter()
    traj_n, wall = nd.native_rollout(g, pol, mot, f, T - 1 - f)
    rm, rn = nd.run_metrics(g, mot, f, traj_m, dt), nd.run_metrics(g, mot, f, traj_n, dt)
    # metric-definition check: recompute joint error / anchor ori error with frame offset 0 (report) and -1 (mjlab)
    dk = mujoco.MjData(m)
    off = {}
    for o in (0, -1):
      je, ae = [], []
      for k in range(1, len(traj_m)):
        t = f + k + o
        je.append(float(np.linalg.norm(traj_m[k][g.qadr] - mot.jp[t])))
        dk.qpos[:] = traj_m[k]
        mujoco.mj_kinematics(m, dk)
        ae.append(nd.quat_angle(mot.bq[t, g.mot_idx[nd.ANCHOR]], dk.xquat[g.bid[nd.ANCHOR]]))
      off[o] = dict(joint_err_norm_mean=float(np.mean(je)), anchor_rot_rad_mean=float(np.mean(ae)))
    online = {k: float(np.mean(v)) for k, v in onl.items()}
    row = dict(start=f, start_s=round(f * dt, 2), mjlab=rm, native=rn, divergence=nd.divergence(g, traj_m, traj_n, dt),
               native_realtime=round(len(traj_n) * dt / wall, 1), metric_check=dict(
                 mjlab_online_means=online, recomputed_offset0=off[0], recomputed_offset_minus1=off[-1],
                 report_joint_rms_times_sqrt29=rm["joint_rms_rad"] * np.sqrt(29)))
    rep_run = next((r for r in rep["runs"] if r["start_frame"] == f), None)
    if rep_run is not None:
      row["report_row"] = dict(mjlab=rep_run["mjlab"], native=rep_run["native"], divergence=rep_run["divergence"])
    cl.append(row)
    print("[closed]", json.dumps(row), flush=True)
  out = dict(clip=a.clip, seed=SEED, facts=facts, equivalence_new_states=results, closed_loop=cl)
  (HERE / f"verify_dance_{a.clip}.json").write_text(json.dumps(out, indent=1, ensure_ascii=False, default=float))
  print("[done]", a.clip, flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--clip", choices=tuple(nd.CLIPS), default="sss")
  a = ap.parse_args()
  torch.set_num_threads(1)
  main(a)
