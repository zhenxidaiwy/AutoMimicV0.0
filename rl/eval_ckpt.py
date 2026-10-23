"""Deterministic evaluation of a tracking checkpoint: play the whole clip once (play config: no obs noise, no pushes,
start at frame 0), record a video, compute tracking metrics, optionally upload to W&B (project g1_dance, group eval).

Usage (unitree_rl_mjlab env, MUJOCO_GL=egl):
  python eval_ckpt.py --ckpt <model_XXXX.pt> --motion <clip.npz> [--wandb] [--task Unitree-G1-Tracking-No-State-Estimation]
Writes <ckpt_dir>/eval/<ckpt_name>.mp4 and .json
"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--wandb", action="store_true")
  ap.add_argument("--extra_steps", type=int, default=25, help="keep running after the clip ends (0.5 s)")
  ap.add_argument("--debug", action="store_true")
  ap.add_argument("--strict", action="store_true", help="keep the training end-effector termination")
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))

  import imageio.v2 as imageio
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls

  device = "cuda:0"
  env_cfg = load_env_cfg(a.task, play=True)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = 1
  env_cfg.commands["motion"].motion_file = str(Path(a.motion).resolve())
  # Evaluation = physical fall only (torso height / orientation). The training-time end-effector rule
  # (wrist/ankle z off by > 25 cm) is counted as a tracking metric instead of ending the episode.
  if not a.strict and "ee_body_pos" in env_cfg.terminations:
    del env_cfg.terminations["ee_body_pos"]
  env = ManagerBasedRlEnv(cfg=env_cfg, device=device, render_mode="rgb_array")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=device)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=device)
  policy = runner.get_inference_policy(device=device)

  cmd = env.command_manager.get_term("motion")
  T = int(cmd.motion.time_step_total)
  env.reset()  # play cfg: sampling_mode="start" -> robot placed at reference frame 0
  obs = venv.get_observations()
  if a.debug:
    tm = env.termination_manager
    print("[debug] after reset: time_step", int(cmd.time_steps[0]), "err_body", float(cmd.metrics["error_body_pos"][0]),
          "robot anchor", cmd.robot_anchor_pos_w[0].tolist(), "ref anchor", cmd.anchor_pos_w[0].tolist())
    with torch.no_grad():
      obs, _, dones, _ = venv.step(policy(obs))
    print("[debug] after 1 step: time_step", int(cmd.time_steps[0]), "dones", dones.tolist(),
          "terms", {n: bool(tm.get_term(n)[0]) for n in tm.active_terms},
          "err_body", float(cmd.metrics["error_body_pos"][0]))
    print("[debug] robot body z", cmd.robot_body_pos_w[0, :, 2].tolist())
    print("[debug] ref   body z", cmd.body_pos_w[0, :, 2].tolist())
    sys.exit(0)
  # Warm-up: the command's relative reference bodies are only computed inside env.step(); the very first termination
  # check after reset compares against zero-initialised buffers (ee_body_pos fires). One step + auto-reset fixes it.
  with torch.no_grad():
    obs, _, _, _ = venv.step(policy(obs))
  frames, err_body, err_anchor_z, err_joint = [], [], [], []
  fell_at, fell_terms, fell_detail = None, [], {}
  ee_names = ("left_ankle_roll_link", "right_ankle_roll_link", "left_wrist_yaw_link", "right_wrist_yaw_link")
  ee_idx = [list(cmd.cfg.body_names).index(n) for n in ee_names]
  ee_violation = []
  for t in range(T + a.extra_steps):
    with torch.no_grad():
      obs, _, dones, _ = venv.step(policy(obs))
    frames.append(env.render())
    err_body.append(float(cmd.metrics["error_body_pos"][0]))
    err_joint.append(float(cmd.metrics["error_joint_pos"][0]))
    err_anchor_z.append(float(torch.abs(cmd.anchor_pos_w[0, 2] - cmd.robot_anchor_pos_w[0, 2])))
    ee_dz = (cmd.body_pos_relative_w[0, ee_idx, 2] - cmd.robot_body_pos_w[0, ee_idx, 2]).abs()
    ee_violation.append(bool((ee_dz > 0.25).any()))
    if bool(env.termination_manager.terminated[0]) and fell_at is None:
      fell_at = t
      tm = env.termination_manager
      fell_terms = [n for n in tm.active_terms if bool(tm.get_term(n)[0])]
      ee = cmd.cfg.body_names
      dz = (cmd.body_pos_relative_w[0, :, 2] - cmd.robot_body_pos_w[0, :, 2]).abs()
      fell_detail = {ee[i]: round(float(dz[i]), 3) for i in range(len(ee)) if float(dz[i]) > 0.15}
      break

  ck = Path(a.ckpt)
  out_dir = ck.parent / "eval"
  out_dir.mkdir(exist_ok=True)
  mp4 = out_dir / f"{ck.stem}.mp4"
  imageio.mimsave(mp4, [f for f in frames if f is not None], fps=int(round(1 / env.step_dt)), macro_block_size=1)
  n = len(err_body)
  res = {"ckpt": str(ck), "motion": a.motion, "clip_steps": T, "steps_run": n,
         "completed_clip": fell_at is None, "fell_at_step": fell_at,
         "fell_at_s": None if fell_at is None else round(fell_at * env.step_dt, 2),
         "termination_terms": fell_terms, "bodies_z_err_gt_15cm": fell_detail,
         "eval_mode": "strict(train terminations)" if a.strict else "fall-only (torso height/orientation)",
         "ee_z_violation_frac": round(float(np.mean(ee_violation)), 3) if ee_violation else None,
         "body_pos_err_mean_m": round(float(np.mean(err_body)), 4),
         "body_pos_err_max_m": round(float(np.max(err_body)), 4),
         "joint_pos_err_mean": round(float(np.mean(err_joint)), 4),
         "anchor_z_err_max_m": round(float(np.max(err_anchor_z)), 4), "video": str(mp4)}
  json.dump(res, open(out_dir / f"{ck.stem}.json", "w"), indent=1)
  print(json.dumps(res))

  if a.wandb:
    import wandb
    run_dir = ck.parent.name
    wdir = Path.home() / "projects" / "dance" / "runs" / "wandb_eval"
    wdir.mkdir(parents=True, exist_ok=True)
    wr = wandb.init(project="g1_dance", group="eval", job_type="eval", name=f"eval_{run_dir}_{ck.stem}",
                    config={"ckpt": str(ck), "train_run": run_dir}, reinit=True, dir=str(wdir))
    wandb.log({"eval/video": wandb.Video(str(mp4), fps=int(round(1 / env.step_dt)), format="mp4"),
               **{f"eval/{k}": v for k, v in res.items() if isinstance(v, (int, float, bool)) and v is not None}})
    print("wandb:", wr.url)
    wr.finish()
  env.close()
