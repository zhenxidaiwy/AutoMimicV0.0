"""Export the exact MuJoCo model mjlab compiles at runtime for the BACKFLIP policies (task
Unitree-G1-Tracking-No-State-Estimation, play cfg, num_envs=1, all randomisation events removed) with the knee effort
limit applied exactly as in training (rl/flip_rewards.set_knee_limit(articulation, 120): the knee joints are split out of
the shared 7520-22 actuator group into their own group with effort_limit 120 N.m; hip roll keeps 139 N.m).

Writes models/flip.mjb, models/flip.xml (MjSpec.to_xml, for other MuJoCo versions), models/flip_info.json (control
facts like dance_info.json) and models/flip_fields.npz (field dump of flip.mjb for the cross-version check), then
verifies: reloaded flip.mjb vs the runtime mj_model (every numeric field), warp (GPU) model knee force range, the
actuator force limits per joint (proves 120 N.m on both knees), and the diff vs the dance export (models/dance.mjb).
Usage (unitree_rl_mjlab env, WSL):  python export_flip_model.py [--knee-limit 120] [--policy backflip_r14_fid2]
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(ROOT / "rl"))
TASK = "Unitree-G1-Tracking-No-State-Estimation"
FIELDS = ("body_mass", "body_ipos", "body_iquat", "body_inertia", "body_pos", "body_quat", "geom_friction", "geom_size",
          "geom_pos", "geom_quat", "geom_solref", "geom_solimp", "geom_margin", "geom_gap", "geom_condim",
          "geom_priority", "geom_contype", "geom_conaffinity", "dof_armature", "dof_damping", "dof_frictionloss",
          "jnt_range", "actuator_gainprm", "actuator_biasprm", "actuator_forcerange", "actuator_forcelimited",
          "actuator_ctrllimited", "actuator_trnid", "actuator_gear", "qpos0")

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--policy", default="backflip_r14_fid2")
  a = ap.parse_args()
  import mujoco
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from flip_rewards import set_knee_limit  # import only (rl/ is not modified)
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.tasks.registry import load_env_cfg

  out = HERE / "models"
  cfg = load_env_cfg(TASK, play=True)
  cfg.scene.num_envs = 1
  cfg.commands["motion"].motion_file = str(ROOT / "policies" / a.policy / "reference_motion.npz")
  removed = [k for k in ("base_com", "encoder_bias", "foot_friction", "push_robot") if cfg.events.pop(k, None) is not None]
  art = cfg.scene.entities["robot"].articulation
  set_knee_limit(art, a.knee_limit)
  groups = [(tuple(c.target_names_expr), c.effort_limit, c.stiffness, c.damping, type(c).__name__) for c in art.actuators]
  print("[cfg] actuator groups after set_knee_limit:", groups, flush=True)
  env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
  m = env.sim.mj_model
  mujoco.mj_saveModel(m, str(out / "flip.mjb"))
  try:
    (out / "flip.xml").write_text(env.scene.spec.to_xml())
    xml_ok = True
  except Exception as e:  # noqa: BLE001
    xml_ok = repr(e)
  r = env.scene["robot"]
  terms = {}
  for name, t in env.action_manager._terms.items():
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
                for g in om._group_obs_term_names}
  info = {
    "task": TASK, "knee_limit": a.knee_limit, "actuator_groups": [[list(g[0]), g[1], g[2], g[3], g[4]] for g in groups],
    "removed_events": removed, "mujoco_version": mujoco.__version__, "timestep": float(m.opt.timestep),
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
  (out / "flip_info.json").write_text(json.dumps(info, indent=1))

  # ---- verification
  mb = mujoco.MjModel.from_binary_path(str(out / "flip.mjb"))
  np.savez(out / "flip_fields.npz", **{f: np.asarray(getattr(mb, f), float) for f in FIELDS})
  diff = {f: float(np.abs(np.asarray(getattr(mb, f), float) - np.asarray(getattr(m, f), float)).max()) for f in FIELDS}
  print("[verify] flip.mjb vs runtime mj_model, max abs per field:", json.dumps(diff), flush=True)
  print("[verify] max over all fields:", max(diff.values()), flush=True)
  print("[verify] opt:", {k: float(getattr(mb.opt, k)) for k in ("timestep", "iterations", "tolerance", "ls_iterations",
                                                                  "ls_tolerance", "impratio", "integrator", "cone",
                                                                  "solver")}, flush=True)
  w_fr = env.sim.model.actuator_forcerange
  w_fr = torch.as_tensor(w_fr).double().cpu().numpy().reshape(-1, m.nu, 2)[0]
  print("[verify] actuator force limits (name | forcelimited | mjb forcerange | warp forcerange | kp | kd):", flush=True)
  for i in range(mb.nu):
    n = mb.actuator(i).name
    print(f"   {n:40s} {int(mb.actuator_forcelimited[i])} {mb.actuator_forcerange[i].tolist()} {w_fr[i].tolist()} "
          f"{mb.actuator_gainprm[i, 0]:.3f} {-mb.actuator_biasprm[i, 2]:.3f}", flush=True)
  knees = [i for i in range(mb.nu) if "knee" in mb.actuator(i).name]
  print("[verify] KNEE actuators:", [(mb.actuator(i).name, mb.actuator_forcerange[i].tolist(), w_fr[i].tolist())
                                     for i in knees], flush=True)
  assert all(np.allclose(np.abs(mb.actuator_forcerange[i]), a.knee_limit) for i in knees), "knee limit not applied"
  assert all(np.allclose(np.abs(w_fr[i]), a.knee_limit) for i in knees), "knee limit not in warp model"
  hr = [i for i in range(mb.nu) if "hip_roll" in mb.actuator(i).name]
  print("[verify] hip roll actuators:", [(mb.actuator(i).name, mb.actuator_forcerange[i].tolist()) for i in hr])
  # vs dance export (same robot, 139 N.m knees): per actuator NAME
  try:
    md = mujoco.MjModel.from_binary_path(str(out / "dance.mjb"))
    by = lambda mm: {mm.actuator(i).name: (mm.actuator_forcerange[i].tolist(), mm.actuator_gainprm[i, 0],
                                           mm.actuator_biasprm[i, :3].tolist()) for i in range(mm.nu)}
    bf, bd = by(mb), by(md)
    changed = {k: (bd[k], bf[k]) for k in bf if str(bf[k]) != str(bd[k])}
    print("[verify] actuators that differ from dance.mjb (by name):", changed, flush=True)
    print("[verify] actuator order flip:", [mb.actuator(i).name for i in range(mb.nu)], flush=True)
    same = {f: float(np.abs(np.asarray(getattr(mb, f), float) - np.asarray(getattr(md, f), float)).max())
            for f in FIELDS if not f.startswith("actuator") and np.asarray(getattr(mb, f)).shape ==
            np.asarray(getattr(md, f)).shape}
    print("[verify] non-actuator fields vs dance.mjb max abs:", max(same.values()), flush=True)
  except Exception as e:  # noqa: BLE001
    print("[verify] dance comparison failed", repr(e))
  print(f"[done] flip.mjb nq {m.nq} nv {m.nv} nu {m.nu}, xml {xml_ok}, removed events {removed}", flush=True)
  env.close()
