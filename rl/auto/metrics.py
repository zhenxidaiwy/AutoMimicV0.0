"""One-shot evaluation of a get-up checkpoint for the self-iterating harness -> JSON.
From random fallen poses (no standing / squat starts): success (pelvis > 0.70 m and torso tilt < 15 deg held 1 s),
time-to-stand per pose, still standing at the end, smoothness (peak joint speed / accel after 0.1 s, peak pelvis |vz|,
max pelvis z), human-likeness (widest feet distance while rising, best squat-template match), final stance (torso /
pelvis tilt, standing-template reward), and the same from a standing start (does it keep the canonical stance?).
Usage (unitree_rl_mjlab env): GETUP_TASK=... [GETUP_KNOBS=...] python metrics.py --ckpt <model.pt> --out m.json
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

POSES = ("supine", "face-down", "left side", "right side")


def rollout(task, ckpt, n, seconds, stand_start):
  import numpy as np
  import torch
  from getup.mdp import squat_template_reward, stand_template_reward, tilt_rad
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  dev = "cuda:0"
  cfg = load_env_cfg(task, play=True)
  cfg.scene.num_envs = n
  if stand_start:
    cfg.events["reset_base"].params["stand_prob"] = 1.0
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(task)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(task) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  dt = env.step_dt
  i_lf, i_rf = robot.body_names.index("left_ankle_roll_link"), robot.body_names.index("right_ankle_roll_link")
  env.reset()
  obs = venv.get_observations()
  steps = int(seconds / dt)
  hold = int(1.0 / dt)
  z0 = env.scene.env_origins[:, 2]
  run_len = torch.zeros(n, device=dev)
  t_stand = torch.full((n,), float("nan"), device=dev)
  peak_qd = torch.zeros(n, device=dev)
  peak_qdd = torch.zeros(n, device=dev)
  peak_vz = torch.zeros(n, device=dev)
  max_z = torch.zeros(n, device=dev)
  peak_feet = torch.zeros(n, device=dev)
  best_squat = torch.zeros(n, device=dev)
  qd_prev = None
  # feet: touchdowns while rising / after standing, foot travel after standing, peak contact force
  sensor = env.scene["feet_ground_contact"]
  stood = torch.zeros(n, dtype=torch.bool, device=dev) | stand_start
  td_rise = torch.zeros(n, device=dev)
  td_stand = torch.zeros(n, device=dev)
  travel = torch.zeros(n, device=dev)
  peak_f = torch.zeros(n, device=dev)
  found_prev, pf_prev = None, None
  # upper-body sway once standing (from 1 s of continuous standing on): torso xy relative to the ankle midpoint in
  # the pelvis yaw frame -> peak-to-peak per axis; torso angular speed RMS
  from mjlab.utils.lab_api.math import quat_apply_inverse, yaw_quat
  i_t = robot.body_names.index("torso_link")
  calm = torch.zeros(n, dtype=torch.bool, device=dev)
  sw_min = torch.full((n, 2), 1e9, device=dev)
  sw_max = torch.full((n, 2), -1e9, device=dev)
  angsq = torch.zeros(n, device=dev)
  calm_steps = torch.zeros(n, device=dev)
  for s in range(steps):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    z = robot.data.root_link_pos_w[:, 2] - z0
    qd = robot.data.joint_vel
    if s * dt >= 0.1:
      peak_qd = torch.maximum(peak_qd, qd.abs().max(1).values)
      if qd_prev is not None:
        peak_qdd = torch.maximum(peak_qdd, ((qd - qd_prev) / dt).abs().max(1).values)
      peak_vz = torch.maximum(peak_vz, robot.data.root_link_lin_vel_w[:, 2].abs())
      max_z = torch.maximum(max_z, z)
    qd_prev = qd.clone()
    bp = robot.data.body_link_pos_w
    feet = torch.norm(bp[:, i_lf, :2] - bp[:, i_rf, :2], dim=1)
    rising = (z > 0.25) & (z < 0.70)
    peak_feet = torch.where(rising, torch.maximum(peak_feet, feet), peak_feet)
    best_squat = torch.maximum(best_squat, squat_template_reward(env))
    up = (z > 0.70) & (torch.rad2deg(tilt_rad(env, "torso_link")) < 15.0)
    stood = stood | up
    found = sensor.data.found.reshape(n, -1)[:, :2] > 0
    pf = bp[:, [i_lf, i_rf], :2]
    if found_prev is not None and s * dt >= 0.1:
      td = (found & ~found_prev).float().sum(1)
      td_rise += td * ((z > 0.30) & ~stood).float()
      td_stand += td * stood.float()
      travel += (pf - pf_prev).norm(dim=-1).sum(1) * stood.float()
      peak_f = torch.maximum(peak_f, sensor.data.force.reshape(n, -1, 3).norm(dim=-1).max(1).values)
    found_prev, pf_prev = found, pf.clone()
    calm = calm | (run_len >= 2 * hold)  # 2 s of continuous standing: settling after rising is not sway
    rel = quat_apply_inverse(yaw_quat(robot.data.root_link_quat_w),
                             bp[:, i_t] - (bp[:, i_lf] + bp[:, i_rf]) / 2)[:, :2]
    cm = calm[:, None]
    sw_min = torch.where(cm, torch.minimum(sw_min, rel), sw_min)
    sw_max = torch.where(cm, torch.maximum(sw_max, rel), sw_max)
    angsq += robot.data.body_link_ang_vel_w[:, i_t].norm(dim=-1) ** 2 * calm.float()
    calm_steps += calm.float()
    run_len = torch.where(up, run_len + 1, torch.zeros_like(run_len))
    newly = (run_len == hold) & torch.isnan(t_stand)
    t_stand = torch.where(newly, torch.full_like(t_stand, (s + 2 - hold) * dt), t_stand)
  z = robot.data.root_link_pos_w[:, 2] - z0
  out = {
    "pose": getattr(env, "_getup_pose", torch.zeros(n, device=dev)).cpu().numpy(),
    "success": (~torch.isnan(t_stand)).cpu().numpy(),
    "t_stand": t_stand.cpu().numpy(),
    "end_standing": (z > 0.6).cpu().numpy(),
    "peak_qd": peak_qd.cpu().numpy(), "peak_qdd": peak_qdd.cpu().numpy(), "peak_vz": peak_vz.cpu().numpy(),
    "max_z": max_z.cpu().numpy(), "peak_feet": peak_feet.cpu().numpy(), "best_squat": best_squat.cpu().numpy(),
    "torso_tilt": torch.rad2deg(tilt_rad(env, "torso_link")).cpu().numpy(),
    "pelvis_tilt": torch.rad2deg(tilt_rad(env, "pelvis")).cpu().numpy(),
    "template": stand_template_reward(env, std=0.06, ang_std=0.35, min_height=0.0).cpu().numpy(),
    "td_rise": td_rise.cpu().numpy(), "td_stand": td_stand.cpu().numpy(), "travel": travel.cpu().numpy(),
    "peak_force": peak_f.cpu().numpy(),
    "sway_pp": torch.where(calm_steps > 50, (sw_max - sw_min).max(dim=1).values * 100,
                           torch.full_like(calm_steps, float("nan"))).cpu().numpy(),
    "torso_angv_rms": torch.where(calm_steps > 50, torch.sqrt(angsq / calm_steps.clamp(min=1)),
                                  torch.full_like(calm_steps, float("nan"))).cpu().numpy(),
  }
  return out


if __name__ == "__main__":
  import os

  import numpy as np
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID

  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--out", required=True)
  ap.add_argument("--n", type=int, default=128)
  ap.add_argument("--seconds", type=float, default=8.0)
  ap.add_argument("--stand_start", action="store_true",
                  help="only the standing-start check (separate process: one env per process)")
  a = ap.parse_args()
  med = lambda x: float(np.nanmedian(x)) if np.isfinite(x).any() else float("nan")
  p90 = lambda x: float(np.nanpercentile(x, 90)) if np.isfinite(x).any() else float("nan")
  if a.stand_start:
    st = rollout(TASK_ID, a.ckpt, 64, 6.0, stand_start=True)
    m = {"stand_start_torso_tilt": med(st["torso_tilt"]), "stand_start_template": med(st["template"]),
         "stand_start_still_standing": float(st["end_standing"].mean()),
         "stand_start_touchdowns": med(st["td_stand"]), "stand_start_foot_travel": med(st["travel"]),
         "stand_start_sway_pp_cm": med(st["sway_pp"]), "stand_start_torso_angv_rms": med(st["torso_angv_rms"])}
    Path(a.out).write_text(json.dumps(m, indent=1))
    print(json.dumps(m, indent=1))
    sys.exit(0)
  r = rollout(TASK_ID, a.ckpt, a.n, a.seconds, stand_start=False)
  ok = r["success"].astype(bool)
  m = {
    "ckpt": a.ckpt, "task": TASK_ID, "knobs": os.environ.get("GETUP_KNOBS", ""), "n": a.n,
    "success": float(ok.mean()), "end_standing": float(r["end_standing"].mean()),
    "t_stand_median": med(r["t_stand"]),
    "per_pose": {},
    "peak_joint_speed_median": med(r["peak_qd"]), "peak_joint_speed_p90": p90(r["peak_qd"]),
    "peak_joint_accel_median": med(r["peak_qdd"]),
    "peak_vz_median": med(r["peak_vz"]), "max_pelvis_z": float(np.max(r["max_z"])),
    "feet_spread_median": med(r["peak_feet"]), "squat_match_median": med(r["best_squat"]),
    "torso_tilt_median": med(r["torso_tilt"][ok]) if ok.any() else float("nan"),
    "pelvis_tilt_median": med(r["pelvis_tilt"][ok]) if ok.any() else float("nan"),
    "template_median": med(r["template"][ok]) if ok.any() else float("nan"),
    "touchdowns_rising_median": med(r["td_rise"]), "touchdowns_after_stand_median": med(r["td_stand"]),
    "foot_travel_after_stand_median": med(r["travel"]), "peak_foot_force_median": med(r["peak_force"]),
    "sway_pp_cm_median": med(r["sway_pp"]), "torso_angv_rms_median": med(r["torso_angv_rms"]),
  }
  for k, name in enumerate(POSES):
    sel = r["pose"] == k
    if sel.any():
      m["per_pose"][name] = {"n": int(sel.sum()), "success": float(r["success"][sel].mean()),
                             "t_stand": med(r["t_stand"][sel])}
  Path(a.out).write_text(json.dumps(m, indent=1))
  print(json.dumps(m, indent=1))
