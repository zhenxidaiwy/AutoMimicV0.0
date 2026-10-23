"""Demo video of the get-up policy: one robot per fallen pose (supine / face-down / left side / right side),
rendered separately at 640x480 and tiled 2x2 with labels.
Usage (unitree_rl_mjlab env, MUJOCO_GL=egl): python demo_getup.py --ckpt <model.pt> --out <video.mp4> [--seconds 6]
"""
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

NAMES = ["supine (on back)", "face-down", "left side", "right side"]

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--out", required=True)
  ap.add_argument("--seconds", type=float, default=6.0)
  ap.add_argument("--title", default="")
  a = ap.parse_args()

  import cv2
  import imageio.v2 as imageio
  import numpy as np
  import torch

  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  dev = "cuda:0"
  agent = load_rl_cfg(TASK_ID)
  panels = []
  for k in range(4):
    cfg = load_env_cfg(TASK_ID, play=True)
    cfg.scene.num_envs = 1
    cfg.episode_length_s = a.seconds + 2
    cfg.events["reset_base"].params["pose"] = k
    cfg.events["reset_base"].params["yaw_range"] = (1.57, 1.57)  # side-on to the default camera
    cfg.viewer.height, cfg.viewer.width = 480, 640
    env = ManagerBasedRlEnv(cfg=cfg, device=dev, render_mode="rgb_array")
    venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
    runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
    runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
    policy = runner.get_inference_policy(device=dev)
    robot = env.scene["robot"]
    env.reset()
    obs = venv.get_observations()
    frames, t_up, up_cnt = [], None, 0
    for s in range(int(a.seconds / env.step_dt)):
      with torch.no_grad():
        obs, _, _, _ = venv.step(policy(obs))
      z = float(robot.data.root_link_pos_w[0, 2] - env.scene.env_origins[0, 2])
      up = float(-robot.data.projected_gravity_b[0, 2])
      up_cnt = up_cnt + 1 if (0.70 < z < 0.90 and up > 0.8) else 0  # standing, not flying
      if t_up is None and up_cnt >= int(1.0 / env.step_dt):
        t_up = (s + 1) * env.step_dt - 1.0
      img = np.ascontiguousarray(env.render())
      t = (s + 1) * env.step_dt
      cv2.putText(img, f"start: {NAMES[k]}", (12, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
      cv2.putText(img, f"t = {t:.1f} s   pelvis {z:.2f} m", (12, 62), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (255, 255, 255), 2)
      if t_up is not None and t >= t_up:
        cv2.putText(img, f"STOOD UP at {t_up:.1f} s", (12, 94), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 255, 80), 2)
      frames.append(img)
    panels.append(frames)
    print(f"{NAMES[k]:<18} stood up at {t_up if t_up is None else round(t_up, 2)} s, final pelvis z {z:.2f} m")
    env.close()
  n = min(len(p) for p in panels)
  fps = int(round(1 / env.step_dt))
  w = imageio.get_writer(a.out, fps=fps, macro_block_size=1, quality=8)
  for i in range(n):
    grid = np.concatenate([np.concatenate([panels[0][i], panels[1][i]], 1),
                           np.concatenate([panels[2][i], panels[3][i]], 1)], 0)
    if a.title:
      bar = np.zeros((40, grid.shape[1], 3), np.uint8)
      cv2.putText(bar, a.title, (12, 28), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
      grid = np.concatenate([bar, grid], 0)
    w.append_data(grid)
  w.close()
  print("video:", a.out)
