"""Evaluate the get-up policy: N envs start in random fallen poses (supine / face-down / left / right side).
Success = pelvis z > 0.70 m AND torso upright (gravity z-component < -0.9 in the body frame) for 1 s continuously.
Reports success rate per initial pose, time-to-stand, and whether the robot is still standing at the end.
Usage (unitree_rl_mjlab env): python eval_getup.py --ckpt <model.pt> [--n 64] [--seconds 10] [--video]
"""
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--seconds", type=float, default=10.0)
  ap.add_argument("--video", action="store_true")
  a = ap.parse_args()

  import imageio.v2 as imageio
  import numpy as np
  import torch

  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = a.n
  cfg.episode_length_s = a.seconds + 1
  env = ManagerBasedRlEnv(cfg=cfg, device=dev, render_mode="rgb_array" if a.video else None)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]

  env.reset()
  obs = venv.get_observations()
  g = robot.data.projected_gravity_b  # gravity in the body frame: upright ~ (0, 0, -1)
  gz0, gx0, gy0 = g[:, 2].clone(), g[:, 0].clone(), g[:, 1].clone()
  # classify the start pose from where gravity points in the pelvis frame
  pose = torch.full((a.n,), -1, device=dev)
  # (before v7e the reset's "supine" was really upside down - gravity along +z of the body - now labelled as such)
  pose[gx0 < -0.7] = 0                                 # supine (on the back): gravity towards the pelvis back
  pose[gx0 > 0.7] = 1                                  # face-down: gravity towards the pelvis front
  pose[(gy0 > 0.7)] = 2
  pose[(gy0 < -0.7)] = 3
  pose[gz0 > 0.7] = 4                                  # upside down (pre-v7e reset)
  names = ["supine", "face-down", "side(+y)", "side(-y)", "upside-down"]

  def up_z():
    """Signed pelvis uprightness = -gravity_z in the body frame: +1 upright, -1 upside down."""
    return -robot.data.projected_gravity_b[:, 2]

  steps = int(a.seconds / env.step_dt)
  up_count = torch.zeros(a.n, device=dev)
  t_stand = torch.full((a.n,), float("nan"), device=dev)
  z_max = torch.zeros(a.n, device=dev)
  vz_max = torch.zeros(a.n, device=dev)
  flight = torch.zeros(a.n, device=dev)
  has_ground_sensor = "robot_ground" in [s.name for s in (cfg.scene.sensors or ())]
  frames = []
  for s in range(steps):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    z_max = torch.maximum(z_max, z)
    vz_max = torch.maximum(vz_max, robot.data.root_link_lin_vel_w[:, 2].abs())
    if has_ground_sensor:
      fnd = env.scene["robot_ground"].data.found
      flight += (fnd.reshape(a.n, -1).sum(dim=1) == 0).float()
    ok = (z > 0.70) & (z < 0.90) & (up_z() > 0.8)  # standing, not flying
    up_count = torch.where(ok, up_count + 1, torch.zeros_like(up_count))
    newly = (up_count >= int(1.0 / env.step_dt)) & torch.isnan(t_stand)
    t_stand[newly] = (s + 1) * env.step_dt - 1.0  # time when the 1 s standing window began
    if a.video and s % 2 == 0:
      frames.append(env.render())
  zend = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
  end_ok = (zend > 0.70) & (zend < 0.90) & (up_z() > 0.8)
  zf = (robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]).cpu().numpy()
  uz = up_z().cpu().numpy()
  print(f"final pelvis z: p10 {np.percentile(zf, 10):.2f} median {np.median(zf):.2f} p90 {np.percentile(zf, 90):.2f} m "
        f"(standing ~0.76) | pelvis up_z (1=upright): median {np.median(uz):.2f}, frac > 0.8: {np.mean(uz > 0.8):.2f}")
  qerr = torch.sqrt(torch.mean(torch.square(robot.data.joint_pos - robot.data.default_joint_pos), dim=1)).cpu().numpy()
  print(f"max pelvis z over episode: median {z_max.median():.2f} max {z_max.max():.2f} m | max |vz|: median "
        f"{vz_max.median():.2f} max {vz_max.max():.2f} m/s | airborne frames: "
        f"{('%.1f%%' % (100 * flight.mean() / steps)) if has_ground_sensor else 'n/a (no robot_ground sensor)'} | "
        f"final joint RMS dev from standing pose: median {np.median(qerr):.2f} rad")
  succ = ~torch.isnan(t_stand)
  print(f"overall: stood up {int(succ.sum())}/{a.n} ({succ.float().mean():.0%}), still standing at the end "
        f"{int(end_ok.sum())}/{a.n}, median time-to-stand {torch.nanmedian(t_stand).item():.2f} s")
  for k, nm in enumerate(names):
    m = pose == k
    if m.any():
      print(f"  {nm:<10} n={int(m.sum()):3d} success {succ[m].float().mean():.0%} "
            f"time {torch.nanmedian(t_stand[m]).item() if succ[m].any() else float('nan'):.2f}s end-standing {end_ok[m].float().mean():.0%}")
  print(f"  unclassified start pose: {int((pose < 0).sum())}")
  if a.video and frames:
    out = Path(a.ckpt).parent / "getup_eval.mp4"
    imageio.mimsave(out, frames, fps=int(round(0.5 / env.step_dt)), macro_block_size=1)
    print("video:", out)
