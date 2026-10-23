"""Quantify upper-body sway after standing (no pushes): from 1 s after the robot has stood up (or from 1 s for a
standing start) to the end, per robot:
- torso (torso_link) horizontal position relative to the ankle midpoint, in the pelvis yaw frame: std and
  peak-to-peak (cm), forward/back (x) and sideways (y); dominant sway frequency (Hz, FFT of the larger axis)
- torso yaw relative to the pelvis (deg std), torso angular velocity RMS (rad/s)
- the joints with the largest position std (which joint is doing the swaying)
Usage (unitree_rl_mjlab env): GETUP_TASK=... python sway_check.py --ckpt <model.pt> [--stand_start]
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
  ap.add_argument("--seconds", type=float, default=10.0)
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
  from mjlab.utils.lab_api.math import quat_apply_inverse, yaw_quat
  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = a.n
  cfg.episode_length_s = a.seconds + 2
  cfg.events.pop("push_robot", None)
  if a.stand_start:
    cfg.events["reset_base"].params["stand_prob"] = 1.0
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  names = list(robot.body_names)
  i_t, i_l, i_r = names.index("torso_link"), names.index("left_ankle_roll_link"), names.index("right_ankle_roll_link")
  dt = env.step_dt
  n = a.n
  env.reset()
  obs = venv.get_observations()
  T = int(a.seconds / dt)
  rel = np.zeros((T, n, 2), np.float32)
  yaw_rel = np.zeros((T, n), np.float32)
  angv = np.zeros((T, n), np.float32)
  qpos = np.zeros((T, n, len(robot.joint_names)), np.float32)
  stood_at = np.full(n, 0 if a.stand_start else -1)
  run = np.zeros(n)
  for s in range(T):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    bp = robot.data.body_link_pos_w
    yq = yaw_quat(robot.data.root_link_quat_w)
    d = quat_apply_inverse(yq, bp[:, i_t] - (bp[:, i_l] + bp[:, i_r]) / 2)
    rel[s] = d[:, :2].cpu().numpy()
    tq = robot.data.body_link_quat_w[:, i_t]
    tyaw = yaw_quat(tq)
    # relative yaw torso vs pelvis
    w = (tyaw[:, 0] * yq[:, 0] + (tyaw[:, 1:] * yq[:, 1:]).sum(-1)).clamp(-1, 1)
    yaw_rel[s] = np.degrees(2 * np.arccos(np.abs(w.cpu().numpy())))
    angv[s] = robot.data.body_link_ang_vel_w[:, i_t].norm(dim=-1).cpu().numpy()
    qpos[s] = robot.data.joint_pos.cpu().numpy()
    z = (robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]).cpu().numpy()
    up = (z > 0.70) & (np.degrees(tilt_rad(env, "torso_link").cpu().numpy()) < 15)
    run = np.where(up, run + 1, 0)
    stood_at = np.where((stood_at < 0) & (run >= int(1.0 / dt)), s, stood_at)
  start = stood_at + int(1.0 / dt)
  ok = (stood_at >= 0) & (start < T - int(2.0 / dt))
  sx, sy, ppx, ppy, fr, yw, av = [], [], [], [], [], [], []
  jstd = []
  for i in np.where(ok)[0]:
    seg = rel[start[i]:, i] * 100  # cm
    seg = seg - seg.mean(0)
    sx.append(seg[:, 0].std()); sy.append(seg[:, 1].std())
    ppx.append(np.ptp(seg[:, 0])); ppy.append(np.ptp(seg[:, 1]))
    ax = 0 if seg[:, 0].std() >= seg[:, 1].std() else 1
    spec = np.abs(np.fft.rfft(seg[:, ax]))
    f = np.fft.rfftfreq(len(seg), dt)
    fr.append(f[1:][np.argmax(spec[1:])])
    yw.append(yaw_rel[start[i]:, i].std())
    av.append(np.sqrt(np.mean(angv[start[i]:, i] ** 2)))
    jstd.append(np.degrees(qpos[start[i]:, i].std(0)))
  st = lambda v: f"median {np.median(v):6.2f}  p90 {np.percentile(v, 90):6.2f}  max {np.max(v):6.2f}"
  print(f"robots analysed: {int(ok.sum())}/{n} ({'standing start' if a.stand_start else 'from falls'}), "
        f"window = 1 s after standing .. {a.seconds:.0f} s")
  print(f"torso sway fore-aft std (cm)     {st(sx)}")
  print(f"torso sway sideways std (cm)     {st(sy)}")
  print(f"torso sway fore-aft p-p (cm)     {st(ppx)}")
  print(f"torso sway sideways p-p (cm)     {st(ppy)}")
  print(f"sway dominant frequency (Hz)     {st(fr)}")
  print(f"torso yaw vs pelvis std (deg)    {st(yw)}")
  print(f"torso angular speed RMS (rad/s)  {st(av)}")
  jm = np.median(np.stack(jstd), 0)
  print("joints moving most while standing (median std, deg):",
        ", ".join(f"{robot.joint_names[k].replace('_joint', '')} {jm[k]:.2f}" for k in np.argsort(-jm)[:6]))
