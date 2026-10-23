"""Compare the dance-tracking env and the get-up env: step dt, joint order, default pose, action scale, obs dims.
Usage (unitree_rl_mjlab env): python compat_probe.py
"""
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(HERE.parent / "rl"))
os.environ.setdefault("GETUP_TASK", "Dance-Recovery-G1-auto")

if __name__ == "__main__":
  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  import getup  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.tasks.registry import load_env_cfg
  out = {}
  for task in ("Unitree-G1-Tracking-No-State-Estimation", "Dance-Recovery-G1-auto"):
    cfg = load_env_cfg(task, play=True)
    cfg.scene.num_envs = 1
    if "motion" in cfg.commands:
      cfg.commands["motion"].motion_file = str(Path.home() / "projects/dance/multi/canon_v1.npz")
    env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
    r = env.scene["robot"]
    at = list(env.action_manager._terms.values())[0]
    scale = getattr(at, "_scale", None)
    out[task] = dict(dt=env.step_dt, physics_dt=env.physics_dt if hasattr(env, "physics_dt") else None,
                     joints=list(r.joint_names), default=r.data.default_joint_pos[0].cpu().numpy(),
                     scale=None if scale is None else (scale[0].cpu().numpy() if torch.is_tensor(scale) else scale),
                     obs={k: tuple(v.shape) for k, v in env.observation_manager.compute().items()},
                     terms=env.observation_manager.active_terms, origin=env.scene.env_origins[0].tolist(),
                     bodies=list(r.body_names)[:3], events=list(cfg.events.keys()),
                     terminations=list(cfg.terminations.keys()), ep_len=cfg.episode_length_s)
    print(f"== {task}: step_dt {out[task]['dt']}, origin {out[task]['origin']}, obs {out[task]['obs']}")
    print("   obs terms:", out[task]["terms"])
    print("   events:", out[task]["events"], " terminations:", out[task]["terminations"], " episode_length_s", out[task]["ep_len"])
    env.close()
  a, b = out.values()
  print("same joint order:", a["joints"] == b["joints"])
  if a["joints"] != b["joints"]:
    print("  tracking:", a["joints"]); print("  getup:   ", b["joints"])
  import numpy as np
  print("default pose max diff (rad):", float(np.abs(a["default"] - b["default"]).max()))
  print("action scale tracking:", a["scale"])
  print("action scale getup:   ", b["scale"])
