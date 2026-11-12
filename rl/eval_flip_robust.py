"""Robustness of a backflip checkpoint (sim-to-real readiness): many envs at once, the clip played from frame 0 with all
terminations off, under perturbation scenarios; per scenario the success rate (rotation >= 330 deg, upright at the
end: tilt < 30 deg, pelvis > 0.6 m) and percentiles of rotation / end tilt.
Scenarios: nominal (play cfg, no perturbation), dr (the training randomisation: pushes, foot friction 0.3-1.2, torso
CoM offset, encoder bias, observation noise), dr + action delay 1 / 2 steps (20 / 40 ms), dr + PD stiffness x0.85.
Usage (unitree_rl_mjlab env): python eval_flip_robust.py --ckpt <model.pt> --motion <clip.npz> [--envs 256]
  [--knee-limit 120] [--scenarios nominal,dr,delay1,delay2,kp085] [--out result.json]"""
import argparse
import dataclasses
import json
import sys
from collections import deque
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"


def cum_rot(q):
  """q (T, N, 4) wxyz -> unwrapped rotation (deg) about each env's dominant axis, (T, N)."""
  import numpy as np
  from scipy.spatial.transform import Rotation as R
  T, N, _ = q.shape
  out = np.zeros((T, N))
  for n in range(N):
    r = R.from_quat(q[:, n][:, [1, 2, 3, 0]])
    inc = (r[:-1].inv() * r[1:]).as_rotvec()
    ax = inc.sum(0)
    ax = ax / (np.linalg.norm(ax) + 1e-9)
    out[1:, n] = np.degrees(np.cumsum(inc @ ax))
  return out


def tilt_deg(q):
  """torso tilt from vertical, q (N, 4) wxyz -> (N,) deg."""
  import numpy as np
  w, x, y, z = q[:, 0], q[:, 1], q[:, 2], q[:, 3]
  zz = 1 - 2 * (x * x + y * y)
  return np.degrees(np.arccos(np.clip(zz, -1, 1)))


def run(a, scen):
  import numpy as np
  import torch
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  nominal = scen == "nominal"
  env_cfg = load_env_cfg(a.task, play=nominal)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = a.envs
  cmd_cfg = env_cfg.commands["motion"]
  # run post_s past the reference, the reference holding its final frame (user 2026-10-23: stays stable?)
  sys.path.insert(0, str(Path(__file__).resolve().parent))
  from mimic_generic import hold_pad_npz
  padded = Path(a.out).with_name(Path(a.out).stem + f"_post_{scen}.npz") if a.out else Path(f"/tmp/post_{scen}.npz")
  n_ref, _ = hold_pad_npz(a.motion, padded, a.post_s) if a.post_s > 0 else (None, None)
  cmd_cfg.motion_file = str(padded.resolve() if a.post_s > 0 else Path(a.motion).resolve())
  cmd_cfg.sampling_mode = "start"  # every env starts at frame 0, standing
  cmd_cfg.pose_range, cmd_cfg.velocity_range = {}, {}
  env_cfg.terminations = {}
  env_cfg.episode_length_s = 1e6
  art = env_cfg.scene.entities["robot"].articulation
  if a.knee_limit is not None:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from flip_rewards import set_knee_limit
    set_knee_limit(art, a.knee_limit)
  if a.hand_friction > 0:
    from mimic_generic import set_hand_friction
    set_hand_friction(env_cfg.scene.entities["robot"], a.hand_friction)
  if scen == "kp085":
    art.actuators = tuple(dataclasses.replace(c, stiffness=c.stiffness * 0.85) for c in art.actuators)
  delay = {"delay1": 1, "delay2": 2}.get(scen, 0)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location="cuda:0")
  policy = runner.get_inference_policy(device="cuda:0")
  cmd = env.command_manager.get_term("motion")
  robot = env.scene["robot"]
  T = int(cmd.motion.time_step_total)
  env.reset()
  obs = venv.get_observations()
  buf = deque()
  quats, pel, pxy, refq = [], [], [], []
  for _ in range(T - 2):
    with torch.no_grad():
      act = policy(obs)
    buf.append(act)
    use = buf.popleft() if len(buf) > delay else torch.zeros_like(act)
    obs, _, _, _ = venv.step(use)
    quats.append(cmd.robot_anchor_quat_w.cpu().numpy())
    refq.append(cmd.anchor_quat_w[:1].cpu().numpy())
    pel.append((robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]).cpu().numpy())
    pxy.append((robot.data.root_link_pos_w[:, :2] - env.scene.env_origins[:, :2]).cpu().numpy())
  quats, pel, pxy = np.array(quats), np.array(pel), np.array(pxy)
  rot = cum_rot(quats)
  # success = full flip AND the whole post_s hold upright, standing, without walking off (drift < 0.3 m)
  nr = (n_ref - 2) if n_ref else len(quats) - 25
  tail = slice(nr, None)
  end_tilt = np.array([tilt_deg(quats[t]) for t in range(len(quats))])[tail].max(0)
  end_pel = pel[tail].min(0)
  drift = np.linalg.norm(pxy[-1] - pxy[nr], axis=-1)
  final_rot = rot[-1]
  # rotation threshold relative to the reference itself (any skill): 0.9 x its own total rotation (backflip 365 ->
  # 329, the former fixed 330; cartwheel_2 ~240 by the same dominant-axis measure)
  ref_rot = float(np.abs(cum_rot(np.array(refq))[-1, 0]))
  base = (np.abs(final_rot) >= 0.9 * ref_rot) & (end_tilt < 30) & (end_pel > 0.6)
  ok = base & (drift < 0.3)  # v1 (kept for comparison with earlier rounds)
  # v2 (decision 2026-10-26, cartwheel_2 r09): under pushes of 0.5 m/s every 1-3 s, 2-4 recovery steps of 0.1-0.15 m
  # in the 5 s window are a correct recovery; 0.3 m allowed about two. 0.5 m still fails walking away.
  ok2 = base & (drift < 0.5) if scen != "nominal" else ok
  env.close()
  pct = lambda x: [round(float(v), 1) for v in np.percentile(x, [5, 50, 95])]
  return {"scenario": scen, "envs": a.envs, "success": round(float(ok.mean()), 3),
          "success_v2": round(float(ok2.mean()), 3),
          "rotation_deg_p5_50_95": pct(np.abs(final_rot)), "end_tilt_deg_p5_50_95": pct(end_tilt),
          "end_pelvis_min_m_p5_50_95": [round(float(v), 3) for v in np.percentile(end_pel, [5, 50, 95])],
          "post_s": a.post_s, "ref_rotation_deg": round(ref_rot, 1), "post_drift_m_p5_50_95": [round(float(v), 3) for v in np.percentile(drift, [5, 50, 95])],
          "fell": round(float((end_pel < 0.4).mean()), 3)}


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--envs", type=int, default=256)
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--hand-friction", type=float, default=0.0)
  ap.add_argument("--scenarios", default="nominal,dr,delay1,delay2,kp085")
  ap.add_argument("--out", default=None)
  ap.add_argument("--post_s", type=float, default=5.0, help="seconds run past the reference (final pose held)")
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  res = []
  for s in a.scenarios.split(","):
    r = run(a, s)
    print(json.dumps(r), flush=True)
    res.append(r)
  if a.out:
    Path(a.out).write_text(json.dumps(res, indent=1))
