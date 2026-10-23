"""Dev diagnostic for native_getup.py: where do single-substep physics differences (mujoco_warp vs C MuJoCo) come from?
For a few states of a get-up rollout: per-env max |dqvel|, worst dof, contact lists (geom pair, dist) in both sims,
actuator saturation, and the same comparison with (a) actuator force limits removed and (b) Euler integrator in BOTH
simulators (to isolate the actuator / implicit-integration path from the contact path).
Usage (unitree_rl_mjlab env, WSL): python diag_getup.py
"""
import os
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from native_getup import KNOBS, POLICY, ROOT, TASK, NativeG1, balanced_lying_reset  # noqa: E402

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(ROOT / "rl"))
os.environ["GETUP_TASK"] = TASK
os.environ["GETUP_KNOBS"] = str(KNOBS)

import mujoco  # noqa: E402
import torch  # noqa: E402

import getup  # noqa: E402,F401
import mjlab.tasks  # noqa: E402,F401
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.managers.event_manager import EventTermCfg  # noqa: E402
from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper  # noqa: E402
from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls  # noqa: E402

dev = "cuda:0"
n = 8
cfg = load_env_cfg(TASK, play=True)
cfg.seed = 0
cfg.scene.num_envs = n
for k in [k for k, v in cfg.events.items() if v.mode in ("startup", "interval")]:
  cfg.events.pop(k)
cfg.events["reset_base"] = EventTermCfg(func=balanced_lying_reset, mode="reset", params=dict(cfg.events["reset_base"].params))
env = ManagerBasedRlEnv(cfg=cfg, device=dev)
agent = load_rl_cfg(TASK)
venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
runner = (load_runner_cls(TASK) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
runner.load(str(POLICY), load_cfg={"actor": True}, strict=True, map_location=dev)
policy = runner.get_inference_policy(device=dev)
sd = env.sim.data
wd = env.sim.wp_data
wm = env.sim.wp_model
nat = NativeG1()
m = nat.m
dof_names = []
for j in range(m.njnt):
  nm = m.joint(j).name
  dof_names += [nm + f"[{i}]" for i in range(6)] if j == 0 else [nm]
gname = lambda g: m.geom(int(g)).name or f"g{int(g)}"  # noqa: E731
print("geom types:", sorted(set((m.geom(i).name, int(m.geom_type[i])) for i in range(m.ngeom) if m.geom_contype[i] or m.geom_conaffinity[i]))[:80])
print("warp contact fields:", [k for k in dir(wd.contact) if not k.startswith("_")])


def warp_step_and_compare(tag, q, v, w, act, envs=range(n), verbose=False):
  sd.qpos[:] = torch.as_tensor(q, dtype=sd.qpos.dtype, device=dev)
  sd.qvel[:] = torch.as_tensor(v, dtype=sd.qvel.dtype, device=dev)
  sd.qacc_warmstart[:] = torch.as_tensor(w, dtype=sd.qacc_warmstart.dtype, device=dev)
  env.action_manager.process_action(act)
  env.action_manager.apply_action()
  env.scene.write_data_to_sim()
  env.sim.step()
  v1 = sd.qvel.cpu().numpy().astype(np.float64)
  nacon = int(wd.nacon.numpy()[0])
  cw = wd.contact.worldid.numpy()[:nacon]
  cg = wd.contact.geom.numpy()[:nacon]
  cd = wd.contact.dist.numpy()[:nacon]
  a_np = act.cpu().numpy().astype(np.float64)
  res = []
  for e in envs:
    nat.set_state(q[e], v[e], w[e])
    nat.d.ctrl[:] = nat.ctrl_from_action(a_np[e])
    mujoco.mj_forward(m, nat.d)
    sat = [m.actuator(i).name.split("/")[-1] for i in range(m.nu)
           if abs(nat.d.actuator_force[i]) >= m.actuator_forcerange[i, 1] - 1e-9]
    ncontacts = sorted((gname(min(c.geom)), gname(max(c.geom)), round(float(c.dist), 6)) for c in nat.d.contact[:nat.d.ncon])
    mujoco.mj_step(m, nat.d)
    dv = np.abs(nat.d.qvel - v1[e])
    k = int(dv.argmax())
    wcontacts = sorted((gname(min(g)), gname(max(g)), round(float(dd), 6)) for g, dd, ww in zip(cg, cd, cw) if ww == e)
    res.append(dv.max())
    print(f"[{tag}] env {e}: max|dv| {dv.max():.2e} at {dof_names[k]} | saturated: {sat}")
    if verbose:
      print("   native contacts:", ncontacts)
      print("   warp   contacts:", wcontacts)
  return res


env.reset()
obs = venv.get_observations()
saved = {}
for s in range(60):
  q = sd.qpos.cpu().numpy().astype(np.float64)
  v = sd.qvel.cpu().numpy().astype(np.float64)
  w = sd.qacc_warmstart.cpu().numpy().astype(np.float64)
  with torch.no_grad():
    act = policy(obs)
  if s in (0, 1, 10, 50):
    saved[s] = (q, v, w, act.clone())
  with torch.no_grad():
    obs, _, _, _ = venv.step(act)

for s in (0, 1):
  print(f"===== step {s}: nominal, contact lists")
  warp_step_and_compare("nominal", *saved[s], verbose=True)

# per-contact parameter comparison for step 0 (state written into warp, forward only)
q, v, w, act = saved[0]
sd.qpos[:] = torch.as_tensor(q, dtype=sd.qpos.dtype, device=dev)
sd.qvel[:] = torch.as_tensor(v, dtype=sd.qvel.dtype, device=dev)
env.sim.forward()
nacon = int(wd.nacon.numpy()[0])
C = {k: getattr(wd.contact, k).numpy()[:nacon] for k in ("worldid", "geom", "dist", "pos", "frame", "friction", "solref",
                                                         "solimp", "includemargin", "dim")}
tangent_mismatch = {}
for e in range(n):
  nat.set_state(q[e], v[e], w[e])
  worst = {}
  nmis = 0
  for c in nat.d.contact[:nat.d.ncon]:
    idx = [i for i in range(nacon) if C["worldid"][i] == e and set(C["geom"][i]) == set(c.geom)
           and abs(C["dist"][i] - c.dist) < 1e-5]
    if not idx:
      worst["unmatched"] = worst.get("unmatched", 0) + 1
      continue
    i = idx[0]
    if np.max(np.abs(c.frame[3:9] - np.ravel(C["frame"][i])[3:9])) > 1e-3:
      nmis += 1
      if nmis == 1:
        print(f"   env {e} example tangent mismatch {gname(min(c.geom))}-{gname(max(c.geom))}: native t1 "
              f"{np.round(c.frame[3:6], 3)} warp t1 {np.round(np.ravel(C['frame'][i])[3:6], 3)} (normal "
              f"{np.round(c.frame[0:3], 3)})")
    for k, nv_, wv in (("pos", c.pos, C["pos"][i]), ("frame_normal", c.frame[0:3], np.ravel(C["frame"][i])[0:3]),
                       ("frame_tangents", c.frame[3:9], np.ravel(C["frame"][i])[3:9]),
                       ("friction", c.friction, C["friction"][i]), ("solref", c.solref, C["solref"][i]),
                       ("solimp", c.solimp, C["solimp"][i]), ("includemargin", [c.includemargin], [C["includemargin"][i]]),
                       ("dim", [c.dim], [C["dim"][i]])):
      worst[k] = max(worst.get(k, 0.0), float(np.max(np.abs(np.asarray(nv_, float) - np.asarray(wv, float)))))
  tangent_mismatch[str(e)] = f"{nmis}/{nat.d.ncon}"
  print(f"[contacts] env {e}: ncon {nat.d.ncon}, tangent-frame mismatches {nmis}, max |native - warp| per contact field: "
        + ", ".join(f"{k} {v_:.1e}" for k, v_ in worst.items()))

# native self-sensitivity: perturb the state by float32 round-off (qpos 1e-7, qvel 1e-6) and step natively
rng = np.random.default_rng(0)
sens = 0.0
for s in (0, 1, 10):
  q, v, w, act = saved[s]
  a_np = act.cpu().numpy().astype(np.float64)
  for e in range(n):
    base = None
    worst = 0.0
    for r in range(6):
      qq = q[e] + (rng.normal(0, 1e-7, q[e].shape) if r else 0)
      vv = v[e] + (rng.normal(0, 1e-6, v[e].shape) if r else 0)
      nat.set_state(qq, vv, w[e])
      nat.d.ctrl[:] = nat.ctrl_from_action(a_np[e])
      mujoco.mj_step(m, nat.d)
      if base is None:
        base = nat.d.qvel.copy()
      else:
        worst = max(worst, float(np.abs(nat.d.qvel - base).max()))
    sens = max(sens, worst)
    print(f"[sensitivity] step {s} env {e}: native max|dqvel| under 1e-7 m / 1e-6 rad/s state noise: {worst:.2e}")

summary = {"what": "single physics substep, same state + qacc_warmstart + ctrl written into mujoco_warp (mjlab) and "
                   "native MuJoCo; max |qvel diff| (rad/s or m/s) per env, 8 envs (2 per fallen pose), seed 0",
           "contact_tangent_frame_mismatch_step0": tangent_mismatch,
           "native_self_sensitivity_max_dqvel": sens, "variants": {}}


def run_variant(tag):
  summary["variants"][tag] = {str(s): [float(x) for x in warp_step_and_compare(tag, *saved[s])] for s in saved}


run_variant("nominal (implicitfast, pyramidal, force limits)")

# (a) no actuator force limits in both sims
m.actuator_forcelimited[:] = 0
wm.actuator_forcelimited.assign(np.zeros(m.nu, dtype=bool))
env.sim.create_graph()
run_variant("no actuator force limits (both)")

# (b) + elliptic friction cone in both (tangent-frame orientation no longer matters)
try:
  m.opt.cone = mujoco.mjtCone.mjCONE_ELLIPTIC
  wm.opt.cone = int(mujoco.mjtCone.mjCONE_ELLIPTIC)
  env.sim.create_graph()
  run_variant("no force limits + elliptic cone (both)")
except Exception as ex:  # noqa: BLE001
  summary["variants"]["no force limits + elliptic cone (both)"] = f"failed: {ex!r}"
  print("elliptic test failed:", repr(ex))
m.opt.cone = mujoco.mjtCone.mjCONE_PYRAMIDAL
m.actuator_forcelimited[:] = 1

# (c) Euler integrator in both, force limits back on, pyramidal
try:
  wm.opt.cone = int(mujoco.mjtCone.mjCONE_PYRAMIDAL)
  wm.actuator_forcelimited.assign(np.ones(m.nu, dtype=bool))
  m.opt.integrator = mujoco.mjtIntegrator.mjINT_EULER
  wm.opt.integrator = int(mujoco.mjtIntegrator.mjINT_EULER)
  env.sim.create_graph()
  run_variant("Euler integrator, force limits, pyramidal (both)")
except Exception as ex:  # noqa: BLE001
  print("euler test failed:", repr(ex))
import json  # noqa: E402
(HERE / "out" / "getup_diag.json").write_text(json.dumps(summary, indent=1))
print("[diag] wrote out/getup_diag.json")
