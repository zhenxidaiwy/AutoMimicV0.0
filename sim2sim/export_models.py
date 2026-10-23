"""Step 1 of sim2sim: export the exact MuJoCo models mjlab compiles at runtime (actuators, armature, friction,
contacts, timestep) for the dance-tracking env and the get-up env, plus the per-env control facts a native
controller needs (decimation, action scale / offset, joint order, default pose, observation layout).
Usage (unitree_rl_mjlab env, WSL):  python export_models.py   ->  ~/dance_win/sim2sim/models/
"""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(HERE.parent / "rl"))
os.environ.setdefault("GETUP_TASK", "Dance-Recovery-G1-auto")
os.environ.setdefault("GETUP_KNOBS", str(HERE.parent / "policies" / "getup_auto_r08" / "knobs.json"))

if __name__ == "__main__":
  import mujoco
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  import getup  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.tasks.registry import load_env_cfg

  out = HERE / "models"
  out.mkdir(exist_ok=True)
  for tag, task in (("dance", "Unitree-G1-Tracking-No-State-Estimation"), ("getup", "Dance-Recovery-G1-auto")):
    cfg = load_env_cfg(task, play=True)
    cfg.scene.num_envs = 1
    if "motion" in cfg.commands:
      cfg.commands["motion"].motion_file = str(Path.home() / "projects/dance/multi/canon_v1.npz")
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
    m = env.sim.mj_model
    mujoco.mj_saveModel(m, str(out / f"{tag}.mjb"))
    try:  # also XML if the scene spec is reachable (for other MuJoCo versions)
      spec = env.scene.spec
      (out / f"{tag}.xml").write_text(spec.to_xml())
      xml_ok = True
    except Exception as e:  # noqa: BLE001
      xml_ok = repr(e)
    r = env.scene["robot"]
    am = env.action_manager
    terms = {}
    for name, t in am._terms.items():
      d = {}
      for k in ("_scale", "_offset", "_clip"):
        v = getattr(t, k, None)
        if v is not None:
          d[k.strip("_")] = (v[0].cpu().numpy().tolist() if torch.is_tensor(v) and v.ndim > 1 else
                             v.cpu().numpy().tolist() if torch.is_tensor(v) else v)
      d["class"] = type(t).__name__
      terms[name] = d
    om = env.observation_manager
    obs_layout = {g: [(n, list(om._group_obs_term_dim[g][i])) for i, n in enumerate(om._group_obs_term_names[g])]
                  for g in om._group_obs_term_names} if hasattr(om, "_group_obs_term_names") else str(om)
    info = {
      "task": task, "mujoco_version": mujoco.__version__, "timestep": float(m.opt.timestep),
      "step_dt": float(env.step_dt), "decimation": int(round(env.step_dt / m.opt.timestep)),
      "nq": int(m.nq), "nv": int(m.nv), "nu": int(m.nu), "nbody": int(m.nbody),
      "joint_names": list(r.joint_names), "body_names": list(r.body_names),
      "actuator_names": [m.actuator(i).name for i in range(m.nu)],
      "actuator_gainprm0": m.actuator_gainprm[:, 0].tolist(), "actuator_biasprm": m.actuator_biasprm[:, :3].tolist(),
      "actuator_trntype": m.actuator_trntype.tolist(), "actuator_forcerange": m.actuator_forcerange.tolist(),
      "dof_armature": m.dof_armature.tolist(), "dof_damping": m.dof_damping.tolist(),
      "dof_frictionloss": m.dof_frictionloss.tolist(),
      "default_joint_pos": r.data.default_joint_pos[0].cpu().numpy().tolist(),
      "action_terms": terms, "obs_layout": obs_layout, "xml_export": xml_ok,
    }
    (out / f"{tag}_info.json").write_text(json.dumps(info, indent=1))
    print(f"[{tag}] {task}: mujoco {mujoco.__version__}, dt {m.opt.timestep} x {info['decimation']} = {env.step_dt}, "
          f"nq {m.nq} nv {m.nv} nu {m.nu}, xml {xml_ok if xml_ok is True else 'FAILED'}")
    print(f"[{tag}] obs: {obs_layout}")
    print(f"[{tag}] action terms: {list(terms)} {[t['class'] for t in terms.values()]}")
    env.close()
