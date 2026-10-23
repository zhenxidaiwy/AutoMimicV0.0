"""Quantify the final standing stance of a get-up policy (after N seconds from random fallen poses):
torso / pelvis tilt, foot placement in the pelvis-yaw frame (fore-aft split, stance width), pelvis height,
residual motion. Also the same numbers for the robot's default standing keyframe as a reference.
Usage (unitree_rl_mjlab env): GETUP_TASK=... python stance_check.py --ckpt <model.pt> [--n 64] [--seconds 8]
"""
import argparse
import math
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--n", type=int, default=64)
  ap.add_argument("--seconds", type=float, default=8.0)
  ap.add_argument("--stand_start", action="store_true",
                  help="start every robot standing in the template pose (v7+ reset) and print how the posture drifts")
  a = ap.parse_args()
  import numpy as np
  import torch
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  from mjlab.utils.lab_api.math import quat_apply_inverse, yaw_quat

  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = a.n
  if a.stand_start:
    cfg.events["reset_base"].params["stand_prob"] = 1.0
  env =ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  names = list(robot.body_names)
  i_torso, i_lf, i_rf = names.index("torso_link"), names.index("left_ankle_roll_link"), names.index("right_ankle_roll_link")
  g = torch.tensor([0.0, 0.0, -1.0], device=dev).repeat(a.n, 1)

  def tilt_deg(q):  # angle between body z axis and world up
    gb = quat_apply_inverse(q, g)
    return torch.rad2deg(torch.acos(torch.clamp(-gb[:, 2], -1, 1)))

  env.reset()
  obs = venv.get_observations()
  steps = int(a.seconds / env.step_dt)
  last_pos = None
  move = []
  for s in range(steps):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    if a.stand_start and s in (0, 10, 25, 50, 100, 200, steps - 1):
      jw = list(robot.joint_names).index("waist_pitch_joint")
      print(f"drift t={(s + 1) * env.step_dt:5.2f}s  pelvis tilt {tilt_deg(robot.data.root_link_quat_w).median():5.1f} deg"
            f"  torso tilt {tilt_deg(robot.data.body_link_quat_w[:, i_torso]).median():5.1f} deg"
            f"  waist pitch {robot.data.joint_pos[:, jw].median():5.2f} rad"
            f"  pelvis gravity x {quat_apply_inverse(robot.data.root_link_quat_w, g)[:, 0].median():5.2f}"
            f" (+ = gravity points to pelvis front = leaning forward)")
    if s >= steps - 50:  # last 1 s: residual pelvis motion
      p = robot.data.root_link_pos_w[:, :2].clone()
      if last_pos is not None:
        move.append(torch.norm(p - last_pos, dim=1))
      last_pos = p
  bq = robot.data.body_link_quat_w
  bp = robot.data.body_link_pos_w
  pel_q, pel_p = robot.data.root_link_quat_w, robot.data.root_link_pos_w
  yq = yaw_quat(pel_q)
  lf = quat_apply_inverse(yq, bp[:, i_lf] - pel_p)
  rf = quat_apply_inverse(yq, bp[:, i_rf] - pel_p)
  standing = (pel_p[:, 2] - env.scene.env_origins[:, 2] > 0.6)
  def s(x):
    x = x[standing].cpu().numpy()
    return f"median {np.median(x):6.2f}  p10 {np.percentile(x, 10):6.2f}  p90 {np.percentile(x, 90):6.2f}"
  print(f"standing robots: {int(standing.sum())}/{a.n}")
  print(f"torso tilt (deg)          {s(tilt_deg(bq[:, i_torso]))}")
  print(f"pelvis tilt (deg)         {s(tilt_deg(pel_q))}")
  print(f"pelvis height (m)         {s(pel_p[:, 2] - env.scene.env_origins[:, 2])}")
  print(f"feet fore-aft split (m)   {s((lf[:, 0] - rf[:, 0]).abs())}   (0 = side by side)")
  print(f"stance width (m)          {s((lf[:, 1] - rf[:, 1]).abs())}")
  print(f"feet center vs pelvis x(m){s(((lf[:, 0] + rf[:, 0]) / 2))}   (0 = pelvis above feet)")
  print(f"pelvis drift last 1 s (m) {s(torch.stack(move).sum(0))}")
  # distance of the key bodies to the canonical standing template (rl/getup/stand_template.npz)
  from getup.mdp import template_rel
  from mjlab.managers.scene_entity_config import SceneEntityCfg
  rel, tmpl = template_rel(env, SceneEntityCfg("robot"))
  per_body = torch.norm(rel - tmpl[None], dim=-1)  # (n, bodies); body 0 = pelvis, 1-2 = shoulders
  print(f"template RMS dist (m)     {s(torch.sqrt(torch.mean(per_body ** 2, dim=1)))}   (0 = exact canonical stance)")
  print(f"  pelvis dist (m)         {s(per_body[:, 0])}")
  print(f"  shoulders dist (m)      {s(per_body[:, 1:3].mean(1))}")
  from getup.mdp import stand_template_reward
  print(f"template reward (0..1)    {s(stand_template_reward(env, std=0.06, ang_std=0.35, min_height=0.0))}")
  jn = list(robot.joint_names)
  for j in ("waist_yaw_joint", "waist_roll_joint", "waist_pitch_joint", "left_knee_joint", "right_knee_joint",
            "left_hip_roll_joint", "right_hip_roll_joint"):
    k = jn.index(j)
    print(f"joint {j:<22}(rad) {s(robot.data.joint_pos[:, k])}   default {float(robot.data.default_joint_pos[0, k]):.2f}")
