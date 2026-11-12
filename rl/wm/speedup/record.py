"""Real mjlab rollout for the S2 fidelity check: writes spec.json (task constants for imagine.py) and logs a
deterministic rollout of a checkpoint: robot state, actor observation, mjlab's per-term step reward, frame, done.
Same env set-up as rl/wm/collect.py (z-only terminations 0.6, hand friction, no pushes / CoM / encoder bias), plus
no observation noise and RSI without pose / velocity / joint noise.
Usage (unitree_rl_mjlab env): python record.py --ckpt <model.pt> --motion <clip.npz> --out <dir> [--envs 256] [--steps 150]"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"
TERMS = ("motion_global_root_pos", "motion_global_root_ori", "motion_body_pos", "motion_body_ori",
         "motion_body_lin_vel", "motion_body_ang_vel", "action_rate_l2", "joint_limit")


def run(a):
  import numpy as np
  import torch
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  env_cfg, agent_cfg = load_env_cfg(a.task), load_rl_cfg(a.task)
  env_cfg.scene.num_envs = a.envs
  cmd_cfg = env_cfg.commands["motion"]
  cmd_cfg.motion_file = str(Path(a.motion).resolve())
  cmd_cfg.sampling_mode = "uniform"
  cmd_cfg.pose_range, cmd_cfg.velocity_range, cmd_cfg.joint_position_range = {}, {}, (0.0, 0.0)
  env_cfg.observations["actor"].enable_corruption = False
  for k in ("push_robot", "base_com", "encoder_bias"):
    env_cfg.events.pop(k, None)
  for k in ("anchor_pos", "ee_body_pos"):
    p = env_cfg.terminations[k].params
    p["threshold"] = max(p["threshold"], 0.6)
  if a.hand_friction > 0:
    from mimic_generic import set_hand_friction
    set_hand_friction(env_cfg.scene.entities["robot"], a.hand_friction)
  from flip_rewards import set_knee_limit
  set_knee_limit(env_cfg.scene.entities["robot"].articulation, a.knee_limit)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location="cuda:0")
  policy = runner.get_inference_policy(device="cuda:0")
  robot, cmd, rm = env.scene["robot"], env.command_manager.get_term("motion"), env.reward_manager
  out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
  spec = {
    "joint_names": list(robot.joint_names), "robot_body_names": list(robot.body_names),
    "tracked_bodies": list(cmd_cfg.body_names), "anchor_body": cmd_cfg.anchor_body_name,
    "ee_bodies": list(env_cfg.terminations["ee_body_pos"].params["body_names"]),
    "default_joint_pos": robot.data.default_joint_pos[0].tolist(),
    "soft_joint_pos_limits": robot.data.soft_joint_pos_limits[0].tolist(),
    "reward_weights": {n: env_cfg.rewards[n].weight for n in TERMS},
    "reward_std": {n: env_cfg.rewards[n].params["std"] for n in TERMS if "std" in env_cfg.rewards[n].params},
    "term_thresholds": {k: env_cfg.terminations[k].params["threshold"] for k in ("anchor_pos", "anchor_ori", "ee_body_pos")},
    "task": a.task, "motion": a.motion, "ckpt": a.ckpt,
  }
  (out / "spec.json").write_text(json.dumps(spec, indent=1))
  names = list(rm._term_names)
  ti = [names.index(n) for n in TERMS]
  d = robot.data
  env.reset()
  obs = venv.get_observations()
  with torch.no_grad():  # warm-up (the first step after reset reports done for every env)
    obs, _, _, _ = venv.step(policy(obs))
  rec = {k: [] for k in ("root_pos", "root_quat", "root_lin_vel", "root_ang_vel", "joint_pos", "joint_vel", "obs",
                         "action", "frame", "reward", "done")}
  for _ in range(a.steps):
    with torch.no_grad():
      act = policy(obs)
      if a.action_noise > 0:  # SuperMimic collection: executed (and stored) action = policy + N(0, sigma^2)
        act = act + a.action_noise * torch.randn_like(act)
    rec["root_pos"].append((d.root_link_pos_w - env.scene.env_origins).cpu())
    rec["root_quat"].append(d.root_link_quat_w.cpu())
    rec["root_lin_vel"].append(d.root_link_lin_vel_w.cpu())
    rec["root_ang_vel"].append(d.root_link_ang_vel_w.cpu())
    rec["joint_pos"].append(d.joint_pos.cpu())
    rec["joint_vel"].append(d.joint_vel.cpu())
    rec["obs"].append((obs["actor"] if hasattr(obs, "keys") else obs).cpu())
    rec["action"].append(act.cpu())
    rec["frame"].append(cmd.time_steps.clone().cpu())
    obs, _, dones, _ = venv.step(act)
    rec["reward"].append(rm._step_reward[:, ti].clone().cpu())  # this step's terms on the new state
    rec["done"].append(dones.bool().cpu())
  np.savez_compressed(out / "real.npz", terms=np.array(TERMS), **{k: torch.stack(v).numpy() for k, v in rec.items()})
  env.close()
  print(json.dumps({"out": str(out), "envs": a.envs, "steps": a.steps}), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--out", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--envs", type=int, default=256)
  ap.add_argument("--steps", type=int, default=150)
  ap.add_argument("--hand-friction", type=float, default=0.6)
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--action-noise", type=float, default=0.0)
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  run(a)
