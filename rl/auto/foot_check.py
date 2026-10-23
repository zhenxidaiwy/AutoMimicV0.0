"""Quantify foot stomping / balance stepping of a get-up policy.
Per robot: foot touchdowns (contact 0 -> 1) while rising (pelvis 0.30-0.70 m) and after standing (from the first
time the pelvis is > 0.70 m with the torso < 15 deg), horizontal foot travel after standing, fraction of standing
time with a foot in the air, and peak foot contact force (impacts). --stand_start: robots start standing.
Usage (unitree_rl_mjlab env): GETUP_TASK=... python foot_check.py --ckpt <model.pt> [--stand_start]
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
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--seconds", type=float, default=8.0)
  ap.add_argument("--stand_start", action="store_true")
  a = ap.parse_args()
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from getup.mdp import tilt_rad
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = a.n
  if a.stand_start:
    cfg.events["reset_base"].params["stand_prob"] = 1.0
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  sensor = env.scene["feet_ground_contact"]
  i_f = [robot.body_names.index("left_ankle_roll_link"), robot.body_names.index("right_ankle_roll_link")]
  dt = env.step_dt
  n = a.n
  env.reset()
  obs = venv.get_observations()
  prev = None
  td_rise = torch.zeros(n, device=dev)
  td_stand = torch.zeros(n, device=dev)
  travel = torch.zeros(n, device=dev)
  air_steps = torch.zeros(n, device=dev)
  stand_steps = torch.zeros(n, device=dev)
  peak_f = torch.zeros(n, device=dev)
  stood = torch.zeros(n, dtype=torch.bool, device=dev) | a.stand_start
  pf_prev = None
  for s in range(int(a.seconds / dt)):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    up = (z > 0.70) & (torch.rad2deg(tilt_rad(env, "torso_link")) < 15.0)
    stood = stood | up
    found = sensor.data.found.reshape(n, -1)[:, :2] > 0
    force = sensor.data.force.reshape(n, 2, -1).norm(dim=-1)
    pf = robot.data.body_link_pos_w[:, i_f, :2]
    if prev is not None and s * dt > 0.1:
      td = (found & ~prev).float().sum(1)
      rising = (z > 0.30) & (z < 0.70) & ~stood
      td_rise += td * rising.float()
      td_stand += td * stood.float()
      travel += (pf - pf_prev).norm(dim=-1).sum(1) * stood.float()
      air_steps += (~found).any(1).float() * stood.float()
      stand_steps += stood.float()
      peak_f = torch.maximum(peak_f, force.max(1).values)
    prev, pf_prev = found, pf.clone()

  def st(x, f=".1f"):
    x = x.cpu().numpy()
    return f"median {np.median(x):{f}}  p90 {np.percentile(x, 90):{f}}  max {x.max():{f}}"
  print(f"robots that stood: {int(stood.sum())}/{n}")
  if not a.stand_start:
    print(f"foot touchdowns while rising          {st(td_rise)}")
  print(f"foot touchdowns after standing        {st(td_stand)}")
  print(f"foot travel after standing (m)        {st(travel, '.2f')}")
  print(f"time with a foot in the air, standing {st(air_steps / stand_steps.clamp(min=1) * 100)} %")
  print(f"peak foot contact force (N)           {st(peak_f, '.0f')}   (robot weight ~ {robot.data.default_mass.sum(-1)[0] * 9.81:.0f} N)"
        if hasattr(robot.data, "default_mass") else f"peak foot contact force (N)           {st(peak_f, '.0f')}")
