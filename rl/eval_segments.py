"""Segment probe (any skill): which parts of the reference has a checkpoint learned?  For each start frame s the
reference is cropped to [s:] (+ post_s held final pose) and every env starts there (the training randomisation on,
terminations off); per start: steps until the robot is LOST (anchor height error > 0.4 m or torso orientation
error > 1.0 rad, the order of the training terminations) and the fraction that is never lost up to the end of the
reference.  A from-frame-0 failure with late starts surviving = the chain is learned backwards, not broken.
Usage (unitree_rl_mjlab env): python eval_segments.py --ckpt <model.pt> --motion <ref.npz> --starts 0,16,46,81,115
  [--envs 64] [--knee-limit 120] [--hand-friction 0.6] [--labels labels.npz] [--out res.json]"""
import argparse
import json
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

REPO = Path.home() / "projects" / "unitree_rl_mjlab"


def crop(src, dst, s):
  z = dict(np.load(src))
  for k, v in z.items():
    if k != "fps" and hasattr(v, "shape") and v.ndim >= 1 and len(v) > s:
      z[k] = v[s:]
  np.savez(dst, **z)
  return len(z["joint_pos"])


def run(a, s):
  import torch
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  from mjlab.utils.lab_api.math import quat_error_magnitude
  sys.path.insert(0, str(Path(__file__).resolve().parent))
  from mimic_generic import hold_pad_npz, set_hand_friction
  from flip_rewards import set_knee_limit
  env_cfg = load_env_cfg(a.task, play=False)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = a.envs
  c = Path(f"/tmp/seg_crop_{s}.npz")
  n_ref = crop(a.motion, c, s)
  p = Path(f"/tmp/seg_post_{s}.npz")
  hold_pad_npz(str(c), p, a.post_s)
  cmd_cfg = env_cfg.commands["motion"]
  cmd_cfg.motion_file = str(p)
  cmd_cfg.sampling_mode = "start"
  cmd_cfg.pose_range, cmd_cfg.velocity_range = {}, {}
  env_cfg.terminations = {}
  env_cfg.episode_length_s = 1e6
  art = env_cfg.scene.entities["robot"].articulation
  set_knee_limit(art, a.knee_limit)
  if a.hand_friction > 0:
    set_hand_friction(env_cfg.scene.entities["robot"], a.hand_friction)
  if a.delay_ms > 0:
    from mimic_generic import add_action_delay
    add_action_delay(art, a.delay_ms, env_cfg.sim.mujoco.timestep)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location="cuda:0")
  policy = runner.get_inference_policy(device="cuda:0")
  cmd = env.command_manager.get_term("motion")
  env.reset()
  obs = venv.get_observations()
  T = n_ref - 2
  lost = torch.full((a.envs,), T, device="cuda:0")

  def up(q):  # world z axis of wxyz quaternions -> body up vector z component frame-free angle helper
    w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
    return torch.stack([2 * (x * z + w * y), 2 * (y * z - w * x), 1 - 2 * (x * x + y * y)], -1)
  for t in range(T):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    dz = (cmd.anchor_pos_w[:, 2] - cmd.robot_anchor_pos_w[:, 2]).abs()
    # after the main event only the TILT counts (heading is free there, as in training: flip_root_ori); r06's land
    # start counted a heading offset of a standing robot as 'lost'
    if s + t >= a.event_frame:
      dq = torch.arccos((up(cmd.anchor_quat_w) * up(cmd.robot_anchor_quat_w)).sum(-1).clamp(-1, 1))
    else:
      dq = quat_error_magnitude(cmd.anchor_quat_w, cmd.robot_anchor_quat_w)
    bad = ((dz > 0.4) | (dq > 1.0)) & (lost == T)
    lost[bad] = t
  env.close()
  lost = lost.cpu().numpy()
  return {"start": s, "frames_to_end": T, "lost_step_p10_50_90": [int(v) for v in np.percentile(lost, [10, 50, 90])],
          "lost_frame_median": int(s + np.median(lost)), "never_lost": round(float((lost == T).mean()), 3)}


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--starts", default="0,16,30,46,60,81,95,115")
  ap.add_argument("--envs", type=int, default=64)
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--hand-friction", type=float, default=0.0)
  ap.add_argument("--delay-ms", type=float, default=0.0)
  ap.add_argument("--labels", default=None)
  ap.add_argument("--post_s", type=float, default=0.5)
  ap.add_argument("--out", default=None)
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  names, ph = None, None
  a.event_frame = 10 ** 9
  if a.labels:
    L = np.load(a.labels)
    names, ph = [str(x) for x in L["phase_names"]], L["phase"]
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from mimic_generic import event_frame
    a.event_frame = event_frame(ph, names)
  res = []
  for s in map(int, a.starts.split(",")):
    r = run(a, s)
    if names is not None:
      r["start_phase"] = names[ph[s]]
      r["lost_phase"] = names[ph[min(r["lost_frame_median"], len(ph) - 1)]]
    print(json.dumps(r), flush=True)
    res.append(r)
  if a.out:
    Path(a.out).write_text(json.dumps(res, indent=1))
