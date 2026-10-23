"""How violent is a get-up policy? From random fallen poses, measure per-joint peak speed / acceleration, action
jumps and pelvis vertical speed over the first `seconds`, and which joints are the worst.
Usage (unitree_rl_mjlab env): GETUP_TASK=... python smooth_check.py --ckpt <model.pt> [--n 64] [--seconds 5]
"""
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--seconds", type=float, default=5.0)
  ap.add_argument("--skip", type=float, default=0.0, help="ignore the first SKIP s (reset transient)")
  ap.add_argument("--pose_extra", type=float, nargs=4, default=None,
                  help="override the reset's extra drop height per pose (supine, face-down, left, right)")
  ap.add_argument("--true_supine", action="store_true")
  a = ap.parse_args()
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
  if a.pose_extra is not None:
    cfg.events["reset_base"].params["pose_extra"] = tuple(a.pose_extra)
  if a.true_supine:
    cfg.events["reset_base"].params["true_supine"] = True
  env =ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  dt = env.step_dt
  env.reset()
  obs = venv.get_observations()
  qd_prev, act_prev = None, None
  peak_qd = torch.zeros(a.n, len(robot.joint_names), device=dev)
  peak_qdd = torch.zeros_like(peak_qd)
  peak_da = torch.zeros(a.n, device=dev)
  peak_vz = torch.zeros(a.n, device=dev)
  fast_steps = torch.zeros(a.n, device=dev)  # steps with any joint faster than 10 rad/s
  trans_vz = torch.zeros(a.n, device=dev)  # peak pelvis |vz| in the first 0.1 s (reset transient)
  i_lf, i_rf = robot.body_names.index("left_ankle_roll_link"), robot.body_names.index("right_ankle_roll_link")
  peak_feet = torch.zeros(a.n, device=dev)  # widest horizontal ankle distance while rising (pelvis 0.25-0.70 m)
  from getup.mdp import squat_template_reward
  best_squat = torch.zeros(a.n, device=dev)  # best match to the squat template while rising (1 = exact squat)
  for s in range(int(a.seconds / dt)):
    with torch.no_grad():
      act = policy(obs)
      obs, _, _, _ = venv.step(act)
    qd = robot.data.joint_vel
    if s * dt < 0.1:
      trans_vz = torch.maximum(trans_vz, robot.data.root_link_lin_vel_w[:, 2].abs())
    if s * dt < a.skip:
      qd_prev, act_prev = qd.clone(), act.clone()
      continue
    peak_qd = torch.maximum(peak_qd, qd.abs())
    if qd_prev is not None and s > 1:  # skip the reset transient
      peak_qdd = torch.maximum(peak_qdd, ((qd - qd_prev) / dt).abs())
      peak_da = torch.maximum(peak_da, (act - act_prev).abs().max(dim=1).values)
    fast_steps += (qd.abs().max(dim=1).values > 10.0).float()
    peak_vz = torch.maximum(peak_vz, robot.data.root_link_lin_vel_w[:, 2].abs())
    bp = robot.data.body_link_pos_w
    z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    rising = (z > 0.25) & (z < 0.70)
    feet = torch.norm(bp[:, i_lf, :2] - bp[:, i_rf, :2], dim=1)
    peak_feet = torch.where(rising, torch.maximum(peak_feet, feet), peak_feet)
    best_squat = torch.maximum(best_squat, squat_template_reward(env))
    qd_prev, act_prev = qd.clone(), act.clone()

  def st(x):
    x = x.cpu().numpy()
    return f"median {np.median(x):7.1f}  p90 {np.percentile(x, 90):7.1f}  max {x.max():7.1f}"
  print(f"peak joint speed, any joint (rad/s)   {st(peak_qd.max(1).values)}")
  print(f"peak joint accel, any joint (rad/s^2) {st(peak_qdd.max(1).values)}")
  print(f"peak action jump per step             {st(peak_da)}")
  print(f"time with a joint > 10 rad/s (s)      {st(fast_steps * dt)}")
  print(f"peak pelvis |vz| (m/s)                {st(peak_vz)}")
  f = peak_feet.cpu().numpy()
  print(f"peak feet distance while rising (m)   median {np.median(f):7.2f}  p90 {np.percentile(f, 90):7.2f}  "
        f"max {f.max():7.2f}   (standing stance 0.24)")
  q = best_squat.cpu().numpy()
  print(f"peak squat-template match (0..1)      median {np.median(q):7.2f}  p10 {np.percentile(q, 10):7.2f}  "
        f"max {q.max():7.2f}   (1 = passes exactly through the deep squat)")
  pose = getattr(env, "_getup_pose", None)
  if pose is not None:
    for k, name in enumerate(("supine", "face-down", "left side", "right side")):
      m = pose == k
      if m.any():
        print(f"reset transient {name:<10} n={int(m.sum()):2d}  peak |vz| first 0.1 s (m/s) {st(trans_vz[m])}")
  med = peak_qd.median(0).values.cpu().numpy()
  medacc = peak_qdd.median(0).values.cpu().numpy()
  order = np.argsort(-med)[:8]
  print("worst joints (median over robots of the per-episode peak):")
  for k in order:
    print(f"  {robot.joint_names[k]:<28} speed {med[k]:5.1f} rad/s   accel {medacc[k]:7.0f} rad/s^2")
