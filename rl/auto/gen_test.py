"""Generalisation test of a get-up policy under initial conditions it was (mostly) not trained on.
Conditions: the 4 trained fallen poses (baseline); random 3D orientation dropped from 0.7 m; large joint noise
(+-0.6 rad, trained +-0.2); tumbling (random root velocity); sitting on the floor; kneeling; low foot friction 0.2;
shifted centre of mass (+-8 cm); a strong push (1.2 m/s) after it has stood up.
Per condition (64 robots, 10 s): stood up (pelvis > 0.70 m, torso < 15 deg, held 1 s), time-to-stand, standing at
the end; for the push: fell and got up again. --video: one robot per condition, 3x3 grid.
Usage (unitree_rl_mjlab env): GETUP_TASK=... python gen_test.py --ckpt <model.pt> --out <video.mp4> [--video]
"""
import argparse
import math
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import torch  # noqa: E402

SIT = {"hip_pitch": -1.5, "knee": 0.3, "ankle_pitch": -0.2, "shoulder_pitch": 0.3, "elbow": 0.6}
KNEEL = {"hip_pitch": 0.0, "knee": 1.6, "ankle_pitch": 0.45, "shoulder_pitch": 0.2, "elbow": 0.6}


def reset_random_orientation(env, env_ids, height=0.7, asset_cfg=None):
  """Uniformly random 3D orientation, dropped from `height` (pelvis), zero velocity."""
  a = env.scene["robot"]
  n = len(env_ids)
  q = torch.randn(n, 4, device=env.device)
  q = q / q.norm(dim=1, keepdim=True)
  pos = env.scene.env_origins[env_ids].clone()
  pos[:, 2] += height
  a.write_root_link_pose_to_sim(torch.cat([pos, q], dim=-1), env_ids=env_ids)
  a.write_root_link_velocity_to_sim(torch.zeros(n, 6, device=env.device), env_ids=env_ids)


def reset_upright(env, env_ids, height=0.25, asset_cfg=None):
  """Pelvis upright at `height`, random yaw (for sitting / kneeling starts)."""
  from mjlab.utils.lab_api.math import quat_from_euler_xyz, sample_uniform
  a = env.scene["robot"]
  n = len(env_ids)
  z = torch.zeros(n, device=env.device)
  q = quat_from_euler_xyz(z, z, sample_uniform(-3.14, 3.14, (n,), env.device))
  pos = env.scene.env_origins[env_ids].clone()
  pos[:, 2] += height
  a.write_root_link_pose_to_sim(torch.cat([pos, q], dim=-1), env_ids=env_ids)
  a.write_root_link_velocity_to_sim(torch.zeros(n, 6, device=env.device), env_ids=env_ids)


def set_joint_pose(env, env_ids, values=None, noise=0.05, asset_cfg=None):
  """Joints whose names end with '<key>_joint' set to values[key] (+ noise); must run after reset_robot_joints."""
  from mjlab.utils.lab_api.math import sample_uniform
  a = env.scene["robot"]
  ids = env_ids.long()
  q = a.data.default_joint_pos[ids].clone()
  for j, name in enumerate(a.joint_names):
    for k, v in values.items():
      if name.endswith(k + "_joint"):
        q[:, j] = v
  q += sample_uniform(-noise, noise, q.shape, env.device)
  lim = a.data.soft_joint_pos_limits[ids]
  q = q.clamp(lim[..., 0], lim[..., 1])
  a.write_joint_state_to_sim(q, torch.zeros_like(q), env_ids=env_ids)


def add_root_velocity(env, env_ids, lin=1.0, ang=3.0, asset_cfg=None):
  """Random root velocity on top of the reset pose (tumbling / still falling)."""
  from mjlab.utils.lab_api.math import sample_uniform
  a = env.scene["robot"]
  n = len(env_ids)
  v = torch.cat([sample_uniform(-lin, lin, (n, 3), env.device), sample_uniform(-ang, ang, (n, 3), env.device)], 1)
  a.write_root_link_velocity_to_sim(v, env_ids=env_ids)


CONDITIONS = [  # (key, label)
  ("trained", "trained fallen poses"),
  ("random_orient", "random 3D orientation, dropped 0.7 m"),
  ("joint_noise", "joint noise +-0.6 rad (trained 0.2)"),
  ("tumbling", "tumbling: root vel 1 m/s, 3 rad/s"),
  ("sitting", "sitting on the floor"),
  ("kneeling", "kneeling"),
  ("low_friction", "foot friction 0.2"),
  ("com_shift", "centre of mass shifted +-8 cm"),
  ("push", "push 1.2 m/s at t = 4.5 s"),
]


def make_cfg(task, key, n, seconds):
  from mjlab.managers.event_manager import EventTermCfg
  from mjlab.tasks.registry import load_env_cfg
  cfg = load_env_cfg(task, play=True)
  cfg.scene.num_envs = n
  cfg.episode_length_s = seconds + 2
  ev = cfg.events
  ev.pop("push_robot", None)  # no random pushes except the explicit push test
  if "reset_base" in ev and "stand_prob" in ev["reset_base"].params:
    ev["reset_base"].params["stand_prob"] = 0.0
  if key == "random_orient":
    ev["reset_base"] = EventTermCfg(func=reset_random_orientation, mode="reset", params={"height": 0.7})
  elif key == "joint_noise":
    ev["reset_robot_joints"].params["position_range"] = (-0.6, 0.6)
  elif key == "tumbling":
    ev["tumble"] = EventTermCfg(func=add_root_velocity, mode="reset", params={"lin": 1.0, "ang": 3.0})
  elif key in ("sitting", "kneeling"):
    ev["reset_base"] = EventTermCfg(func=reset_upright, mode="reset",
                                    params={"height": 0.25 if key == "sitting" else 0.55})
    ev["pose"] = EventTermCfg(func=set_joint_pose, mode="reset",
                              params={"values": SIT if key == "sitting" else KNEEL, "noise": 0.05})
  elif key == "low_friction":
    if "foot_friction" in ev:
      ev["foot_friction"].params["ranges"] = (0.2, 0.2)
  elif key == "com_shift":
    if "base_com" in ev:
      ev["base_com"].params["ranges"] = {0: (-0.08, 0.08), 1: (-0.08, 0.08), 2: (-0.05, 0.05)}
  return cfg


def run(task, ckpt, key, n, seconds, render=False):
  import numpy as np
  from getup.mdp import tilt_rad
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_rl_cfg, load_runner_cls
  dev = "cuda:0"
  cfg = make_cfg(task, key, n, seconds)
  if render:
    cfg.viewer.height, cfg.viewer.width = 360, 480
  env = ManagerBasedRlEnv(cfg=cfg, device=dev, render_mode="rgb_array" if render else None)
  agent = load_rl_cfg(task)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(task) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  dt = env.step_dt
  env.reset()
  obs = venv.get_observations()
  hold = int(1.0 / dt)
  run_len = torch.zeros(n, device=dev)
  t_stand = torch.full((n,), float("nan"), device=dev)
  fell_after_push = torch.zeros(n, dtype=torch.bool, device=dev)
  t_up_after = torch.full((n,), float("nan"), device=dev)
  push_step = int(4.5 / dt)
  frames = []
  for s in range(int(seconds / dt)):
    if key == "push" and s == push_step:
      ang = torch.rand(n, device=dev) * 2 * math.pi
      v = torch.zeros(n, 6, device=dev)
      v[:, 0], v[:, 1] = 1.2 * torch.cos(ang), 1.2 * torch.sin(ang)
      robot.write_root_link_velocity_to_sim(v)
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    up = (z > 0.70) & (torch.rad2deg(tilt_rad(env, "torso_link")) < 15.0)
    run_len = torch.where(up, run_len + 1, torch.zeros_like(run_len))
    newly = (run_len == hold) & torch.isnan(t_stand)
    t_stand = torch.where(newly, torch.full_like(t_stand, (s + 2 - hold) * dt), t_stand)
    if key == "push" and s > push_step:
      fell_after_push |= z < 0.45
      back = fell_after_push & (run_len == hold) & torch.isnan(t_up_after)
      t_up_after = torch.where(back, torch.full_like(t_up_after, (s + 2 - hold) * dt), t_up_after)
    if render:
      import cv2
      img = np.ascontiguousarray(env.render())
      lab = dict(CONDITIONS)[key]
      cv2.putText(img, lab, (8, 22), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
      cv2.putText(img, f"t = {(s + 1) * dt:.1f} s  pelvis {float(z[0]):.2f} m", (8, 44),
                  cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
      if not math.isnan(float(t_stand[0])) and (s + 1) * dt >= float(t_stand[0]):
        cv2.putText(img, f"STOOD UP at {float(t_stand[0]):.1f} s", (8, 66), cv2.FONT_HERSHEY_SIMPLEX, 0.55,
                    (80, 255, 80), 2)
      if key == "push" and s >= push_step and s < push_step + 25:
        cv2.putText(img, "PUSH!", (8, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (80, 80, 255), 2)
      frames.append(img)
  end = (robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]) > 0.6
  env.close()
  res = {"success": (~torch.isnan(t_stand)).float().mean().item(),
         "t_med": float(np.nanmedian(t_stand.cpu().numpy())) if (~torch.isnan(t_stand)).any() else float("nan"),
         "end": end.float().mean().item()}
  if key == "push":
    res["fell"] = fell_after_push.float().mean().item()
    res["recovered"] = ((fell_after_push & end).float().sum() / fell_after_push.float().sum().clamp(min=1)).item()
  return res, frames


if __name__ == "__main__":
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--out", default="")
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--seconds", type=float, default=10.0)
  ap.add_argument("--video", action="store_true")
  a = ap.parse_args()
  print(f"{'condition':<40} {'stood up':>9} {'t median':>9} {'standing at end':>16}")
  for key, label in CONDITIONS:
    r, _ = run(TASK_ID, a.ckpt, key, a.n, a.seconds)
    extra = f"   fell after push {r['fell']:.0%}, of those got up again {r['recovered']:.0%}" if key == "push" else ""
    print(f"{label:<40} {r['success']:>9.0%} {r['t_med']:>8.2f}s {r['end']:>16.0%}{extra}", flush=True)
  if a.video:
    import imageio.v2 as imageio
    import numpy as np
    panels = []
    for key, _ in CONDITIONS:
      _, fr = run(TASK_ID, a.ckpt, key, 1, 9.0, render=True)
      panels.append(fr)
    m = min(len(p) for p in panels)
    w = imageio.get_writer(a.out, fps=int(round(1 / 0.02)), macro_block_size=1, quality=8)
    for i in range(m):
      rows = [np.concatenate([panels[3 * r_ + c][i] for c in range(3)], 1) for r_ in range(3)]
      w.append_data(np.concatenate(rows, 0))
    w.close()
    print("video:", a.out)
