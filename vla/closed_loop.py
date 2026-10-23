"""Closed loop: real (held-out) human video keypoints -> WatchNet (10 Hz) -> reference buffer -> tracker policy (50 Hz).

The tracker's motion buffers are overwritten online with the high-level predictions:
  joint_pos <- predicted chunk, joint_vel <- finite difference, torso (anchor) quat <- predicted orientation
  composed with the integrated reference yaw. Body positions keep the clip's offline ground truth (GVHMR+GMR of the
  same video) so the command's error metrics measure following error vs ground truth.
All training terminations are disabled; a fall = torso height < 0.45 m or tilt > 60 deg.

Usage (unitree_rl_mjlab env):
  python closed_loop.py --clip gym_sss --watch v1_aux_s0 --ckpt <tracker.pt> [--latency 5] [--video]
                        [--mode model|oracle|shadow]   oracle = feed ground-truth reference (upper bound)
"""
import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = Path.home() / "projects" / "unitree_rl_mjlab"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rl"))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--clip", required=True)
  ap.add_argument("--watch", default="v1_aux_s0")
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--latency", type=int, default=5, help="perception+inference latency in 50 Hz steps")
  ap.add_argument("--mode", default="model", choices=["model", "oracle"])
  ap.add_argument("--video", action="store_true")
  ap.add_argument("--tag", default="")
  a = ap.parse_args()

  from dataclasses import asdict

  import numpy as np
  import torch
  from scipy.spatial.transform import Rotation as Rot

  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  from data import DS, PHASES, TORSO, build_clip, normalise
  from model import WatchNet

  dev = "cuda:0"
  clip = build_clip(a.clip, 0)  # real view only
  kp = clip["kp"][0]
  Th = kp.shape[0]
  gt_npz = DS / a.clip / "g1_lock_vlm_50fps.npz"

  env_cfg = load_env_cfg(a.task, play=True)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = 1
  env_cfg.terminations = {}
  env_cfg.commands["motion"].motion_file = str(gt_npz)
  env = ManagerBasedRlEnv(cfg=env_cfg, device=dev, render_mode="rgb_array" if a.video else None)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  cmd = env.command_manager.get_term("motion")
  mot = cmd.motion
  T50 = int(mot.time_step_total)
  aidx = cmd.motion_anchor_body_index
  gt_jpos = mot.joint_pos.clone()
  gt_quat = mot.body_quat_w[:, aidx].clone()

  ws = torch.load(Path.home() / "projects/dance/vla/runs" / a.watch / "model.pt", weights_only=False)
  wargs = ws["args"]
  W, H = wargs.get("W", 30), wargs.get("H", 25)
  net = WatchNet(W=W, H=H, aux=not wargs.get("no_aux", False)).to(dev).eval()
  net.load_state_dict(ws["model"])
  lead = wargs.get("lead", 0)
  every = 1 if H == 1 else 5  # shadowing baseline updates every step; chunked model at 10 Hz

  prev_jp = [None]

  def yaw_of(q_wxyz):
    R = Rot.from_quat(np.r_[q_wxyz[1:], q_wxyz[0]]).as_matrix()
    return np.arctan2(R[1, 0], R[0, 0])

  def write_chunk(step0, chunk, yaw_ref):
    """chunk (H, 35): joint_pos(29) + rot6d of torso relative to the current reference yaw."""
    H = chunk.shape[0]
    idx = torch.arange(step0, step0 + H, device=dev).clamp(max=T50 - 1)
    jp = torch.tensor(chunk[:, :29], device=dev)
    r6 = chunk[:, 29:35].reshape(H, 3, 2)  # rot6d = first two columns of R, stored row-major (3x2)
    b1 = r6[..., 0] / np.linalg.norm(r6[..., 0], axis=-1, keepdims=True)
    b2 = r6[..., 1] - (b1 * r6[..., 1]).sum(-1, keepdims=True) * b1
    b2 /= np.linalg.norm(b2, axis=-1, keepdims=True)
    Rrel = np.stack([b1, b2, np.cross(b1, b2)], -1)
    Rw = Rot.from_euler("z", yaw_ref).as_matrix() @ Rrel
    q = Rot.from_matrix(Rw).as_quat()[:, [3, 0, 1, 2]]
    mot.joint_pos[idx] = jp
    mot.body_quat_w[idx, aidx] = torch.tensor(q, dtype=torch.float32, device=dev)
    jv = torch.zeros_like(jp)
    if H > 1:
      jv[1:] = (jp[1:] - jp[:-1]) / env.step_dt
      jv[0] = jv[1]
    elif prev_jp[0] is not None:  # single-frame (shadowing) output: velocity from consecutive predictions
      jv[0] = (jp[0] - prev_jp[0]) / env.step_dt
    prev_jp[0] = jp[-1].clone()
    mot.joint_vel[idx] = jv

  def predict(h):
    idx = np.clip(np.arange(h - W + 1, h + 1), 0, Th - 1)
    x = torch.tensor(normalise(kp[idx]).reshape(1, W, -1), device=dev)  # same normalisation as training
    with torch.no_grad():
      o = net(x)
    info = {}
    if "dance" in o:
      info = {"dance": int(o["dance"].argmax()), "dance_p": float(o["dance"].softmax(-1).max()),
              "phase": PHASES[int(o["phase"].argmax())]}
    return o["chunk"][0].cpu().numpy(), info

  # initial reference: model prediction from the first frame (oracle: ground truth)
  yaw_ref = yaw_of(gt_quat[0].cpu().numpy())
  if a.mode == "model":
    ch, _ = predict(0)
    write_chunk(0, ch, yaw_ref)
  env.reset()
  obs = venv.get_observations()
  with torch.no_grad():
    obs, _, _, _ = venv.step(policy(obs))  # warm-up step (relative buffers, see rl/eval_ckpt.py)

  steps = min(T50, int(Th / 30 * 50))
  frames, logs, fell = [], [], None
  pending = []  # (apply_at_step, chunk, yaw)
  for s in range(steps):
    if a.mode == "model" and s % every == 0:  # 10 Hz high level (every step for the shadowing baseline)
      h = min(int(s * env.step_dt * 30), Th - 1)
      ch, info = predict(h)
      # prediction made at step s targets robot steps s+lead...; it becomes available at s+latency
      cur = min(s + a.latency, T50 - 1)
      yaw_ref = yaw_of(mot.body_quat_w[cur, aidx].cpu().numpy())
      pending.append((s + a.latency, s + lead, ch, yaw_ref, info))
    while pending and pending[0][0] <= s:
      _, target0, ch, yr, info = pending.pop(0)
      off = s - target0  # chunk index aligned to the current step
      if off < ch.shape[0]:
        write_chunk(s, ch[max(off, 0):], yr)
      logs.append({"step": s, **info})
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    t = int(cmd.time_steps[0])
    z = float(cmd.robot_anchor_pos_w[0, 2])
    qa = cmd.robot_anchor_quat_w[0].cpu().numpy()
    up = Rot.from_quat(np.r_[qa[1:], qa[0]]).apply([0, 0, 1])[2]
    err_gt = float((cmd.robot_joint_pos[0] - gt_jpos[min(t, T50 - 1)]).abs().mean())
    logs.append({"step": s, "torso_z": z, "joint_err_vs_gt": err_gt, "body_pos_err": float(cmd.metrics["error_body_pos"][0])})
    if a.video:
      frames.append(env.render())
    if fell is None and (z < 0.45 or up < 0.5):
      fell = s
      break

  errs = [l["joint_err_vs_gt"] for l in logs if "joint_err_vs_gt" in l]
  bpe = [l["body_pos_err"] for l in logs if "body_pos_err" in l]
  dances = [l["dance"] for l in logs if "dance" in l]
  res = {"clip": a.clip, "mode": a.mode, "watch": a.watch, "latency_steps": a.latency, "lead_steps": lead,
         "steps": steps, "completed": fell is None, "fell_at_s": None if fell is None else round(fell * env.step_dt, 2),
         "joint_err_vs_gt_mean": round(float(np.mean(errs)), 4), "body_pos_err_vs_gt_mean": round(float(np.mean(bpe)), 4),
         "dance_pred_frac_sss": round(float(np.mean([d == 0 for d in dances])), 3) if dances else None}
  out = Path.home() / "projects/dance/vla/closed_loop"
  out.mkdir(parents=True, exist_ok=True)
  name = f"{a.clip}_{a.mode}_{a.watch}_lat{a.latency}{a.tag}"
  json.dump({"result": res, "log": logs}, open(out / f"{name}.json", "w"))
  if a.video and frames:
    import imageio.v2 as imageio
    imageio.mimsave(out / f"{name}.mp4", frames, fps=50, macro_block_size=1)
  print(json.dumps(res))
