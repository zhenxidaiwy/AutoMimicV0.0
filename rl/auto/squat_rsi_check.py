"""Sanity check of the squat RSI: all envs start in the squat template; print squat match, pelvis height and torso
tilt over the first seconds (does the policy rise from the squat, fall, or sit down?).
Usage (unitree_rl_mjlab env): GETUP_TASK=Dance-Recovery-G1-auto python squat_rsi_check.py --ckpt <model.pt>
"""
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  a = ap.parse_args()
  import torch
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from getup.mdp import squat_template_reward, tilt_rad
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = 32
  cfg.events["reset_base"].params.update(stand_prob=0.0, squat_prob=1.0)
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  env.reset()
  obs = venv.get_observations()
  for s in range(200):
    if s in (0, 5, 15, 25, 50, 100, 199):
      z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
      print(f"t={s * env.step_dt:4.2f}s squat match {squat_template_reward(env).median():.2f}  pelvis z {z.median():.2f} m"
            f"  torso tilt {torch.rad2deg(tilt_rad(env, 'torso_link')).median():5.1f} deg")
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
