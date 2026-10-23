"""Check the hold-pose delay fix: fixed lag 4 physics steps, reset, one env step with zero action; print the joint
position targets (data.ctrl) the actuators received. Bug: ~0 rad; fix: the robot's current joint positions.
Usage (unitree_rl_mjlab env): python test_delay_fix.py"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import mjlab.tasks  # noqa: F401,E402
import src.tasks  # noqa: F401,E402
import torch  # noqa: E402
from mjlab.actuator.delayed_actuator import DelayedActuatorCfg  # noqa: E402
from mjlab.envs import ManagerBasedRlEnv  # noqa: E402
from mjlab.tasks.registry import load_env_cfg  # noqa: E402

import mimic_generic as mg  # noqa: E402

MOTION = str(Path.home() / "projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz")
for name, cls in (("mjlab DelayedActuatorCfg", DelayedActuatorCfg), ("HoldDelayedActuatorCfg", mg._hold_delay_cfg())):
  cfg = load_env_cfg("Unitree-G1-Tracking-No-State-Estimation", play=True)
  cfg.scene.num_envs = 2
  cfg.commands["motion"].motion_file = MOTION
  art = cfg.scene.entities["robot"].articulation
  mg.set_knee_limit(art, 120.0)
  art.actuators = tuple(cls(base_cfg=c, delay_target="position", delay_min_lag=4, delay_max_lag=4) for c in art.actuators)
  env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
  env.reset()
  env.step(torch.zeros(2, env.action_manager.total_action_dim, device="cuda:0"))
  ctrl = env.sim.data.ctrl[0].cpu()
  q = env.scene["robot"].data.joint_pos[0].cpu()
  print(f"{name:28s} |ctrl| mean {ctrl.abs().mean():.3f}  max {ctrl.abs().max():.3f}  |q| mean {q.abs().mean():.3f}"
        f"  mean |ctrl - q| {(ctrl[:len(q)] - q).abs().mean():.3f}")
  env.close()
