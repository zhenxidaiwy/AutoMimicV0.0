"""Verifier root-cause probe: at the pushed state of verify_getup_check.py (seed 123, step 200), how much of the
single-substep mujoco_warp vs C-MuJoCo difference is due to the implicitfast actuator-damping derivative of
force-SATURATED position actuators? Compare one substep in both sims with (a) nominal, (b) Euler integrator in both,
(c) actuator force limits off in both. Writes verify_getup_out/satdiag.json."""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from verify_getup_check import DEV, VOUT, MyNative, make_env, mapping_from_env  # noqa: E402

import mujoco  # noqa: E402
import torch  # noqa: E402
from tensordict import TensorDict  # noqa: E402

N, SEED, PUSH = 32, 123, 200
env, venv, policy, _ = make_env(N, SEED, balanced=False)
mp = mapping_from_env(env)
nat = MyNative(mp)
m = nat.m
sd = env.sim.data
wm = env.sim.wp_model
rng = np.random.default_rng(SEED)


def snap():
  return (sd.qpos.cpu().numpy().astype(np.float64), sd.qvel.cpu().numpy().astype(np.float64),
          sd.qacc_warmstart.cpu().numpy().astype(np.float64))


def write(q, v, w):
  sd.qpos[:] = torch.as_tensor(q, dtype=sd.qpos.dtype, device=DEV)
  sd.qvel[:] = torch.as_tensor(v, dtype=sd.qvel.dtype, device=DEV)
  sd.qacc_warmstart[:] = torch.as_tensor(w, dtype=sd.qacc_warmstart.dtype, device=DEV)


env.reset()
obs = venv.get_observations()
states = {}
for s in range(PUSH + 6):
  if s == PUSH:
    q, v, w = snap()
    jr = m.jnt_range[1:]
    qadr = m.jnt_qposadr[1:]
    q[:, qadr] = np.clip(q[:, qadr] + rng.uniform(-0.3, 0.3, (N, len(qadr))), jr[:, 0] + 0.02, jr[:, 1] - 0.02)
    v[:, 0:3] += rng.uniform(-1.0, 1.0, (N, 3))
    v[:, 3:6] += rng.uniform(-2.0, 2.0, (N, 3))
    v[:, 6:] += rng.normal(0, 1.5, (N, v.shape[1] - 6))
    write(q, v, w)
    env.sim.forward()
    obs = TensorDict(env.observation_manager.compute(update_history=True), batch_size=[N])
  with torch.no_grad():
    act = policy(obs)
  if s in (0, PUSH, PUSH + 1, PUSH + 5):
    states[s] = (*snap(), act.clone())
  with torch.no_grad():
    obs, _, _, _ = venv.step(act)


def compare(tag):
  out = {}
  for s, (q, v, w, act) in states.items():
    write(q, v, w)
    env.action_manager.process_action(act)
    env.action_manager.apply_action()
    env.scene.write_data_to_sim()
    env.sim.step()
    v1 = sd.qvel.cpu().numpy().astype(np.float64)
    a_np = act.cpu().numpy().astype(np.float64)
    dv, nsat, worst_sat = [], [], []
    for e in range(N):
      nat.set_state(q[e], v[e], w[e])
      nat.d.ctrl[:] = nat.ctrl(a_np[e])
      mujoco.mj_forward(m, nat.d)
      sat = np.abs(nat.d.actuator_force) >= m.actuator_forcerange[:, 1] - 1e-9
      nsat.append(int(sat.sum()))
      mujoco.mj_step(m, nat.d)
      dd = np.abs(nat.d.qvel - v1[e])
      dv.append(float(dd.max()))
      j = int(dd.argmax())
      acts = [i for i in range(m.nu) if int(m.actuator_trnid[i, 0]) >= 1 and m.jnt_dofadr[int(m.actuator_trnid[i, 0])] == j]
      worst_sat.append(bool(acts and sat[acts[0]]))
    out[str(s)] = {"dv_max": max(dv), "dv_median": float(np.median(dv)), "n_saturated_actuators_median": float(np.median(nsat)),
                   "frac_envs_worst_dof_actuator_saturated": float(np.mean(worst_sat))}
    print(f"[{tag}] step {s}: max|dv| {max(dv):.2e} median {np.median(dv):.2e} | saturated actuators/env median "
          f"{np.median(nsat):.0f} | worst dof's actuator saturated in {np.mean(worst_sat):.0%} of envs", flush=True)
  return out


res = {"nominal": compare("nominal")}
m.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
wm.opt.integrator = int(mujoco.mjtIntegrator.mjINT_EULER)
env.sim.create_graph()
res["euler_both"] = compare("euler both")
m.opt.integrator = mujoco.mjtIntegrator.mjINT_IMPLICITFAST
wm.opt.integrator = int(mujoco.mjtIntegrator.mjINT_IMPLICITFAST)
m.actuator_forcelimited[:] = 0
wm.actuator_forcelimited.assign(np.zeros(m.nu, dtype=bool))
env.sim.create_graph()
res["no_forcelimit_both"] = compare("no force limits both")
(VOUT / "satdiag.json").write_text(json.dumps(res, indent=1))
print("[satdiag] wrote", VOUT / "satdiag.json")
