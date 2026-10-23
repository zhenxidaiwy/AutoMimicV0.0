"""Closed loop with skill retrieval: human video keypoints -> RetrieveNet (10 Hz) -> canonical frame -> playback
controller -> tracker (50 Hz) tracking the CANONICAL high-quality reference (canon_v1.npz: 闪身步 + 狗熊哆嗦毛).

Modes: model (RetrieveNet), oracle_align (ground-truth VLM-label alignment of the test clip = perfect perception).
Usage (unitree_rl_mjlab env):
  python retrieve_loop.py --clip gym_sss --watch ret_lead0_s0 --ckpt <tracker.pt> [--latency 5] [--video]
Metrics: completed / fell_at_s, track_err (robot vs the canonical reference it plays = motion quality),
phase_sync (robot canonical phase == human VLM phase), flash_lag_s (human flash onsets vs robot flash onsets).
"""
import argparse
import dataclasses
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "rl"))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--clip", required=True)
  ap.add_argument("--watch", default="ret_lead0_s0")
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", default=str(Path.home() / "projects/dance/multi/canon_v1.npz"))
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--latency", type=int, default=5)
  ap.add_argument("--mode", default="model", choices=["model", "oracle_align"])
  ap.add_argument("--video", action="store_true")
  ap.add_argument("--tag", default="")
  ap.add_argument("--speed", type=float, default=1.0, help="playback speed of the human video (0.5 = half speed)")
  ap.add_argument("--kp", default="vit", choices=["vit", "yolo"], help="keypoint source for the human video")
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
  from align import align, to_class
  from data import DS, PHASES, build_clip, normalise
  from phase_rsi import PhaseMotionCommandCfg
  from train_retrieve import CANON_PHASE, STATE_DANCE, STATE_FRAME, TABLE, RetrieveNet

  dev = "cuda:0"
  clip = build_clip(a.clip, 0, causal=True, source=a.kp)  # what the robot would see frame by frame
  kp, Th = clip["kp"][0], clip["kp"].shape[1]
  human_phase = [PHASES[i] for i in clip["phase"]]
  if a.speed != 1.0:
    # the camera still runs at 30 fps; the person moves at `speed`: resample the keypoint track in time
    Tn = int(round(Th / a.speed))
    src = np.arange(Tn) * a.speed
    i0 = np.floor(src).astype(int).clip(0, Th - 1)
    i1 = (i0 + 1).clip(0, Th - 1)
    w = (src - i0)[:, None, None]
    kp = ((1 - w) * kp[i0] + w * kp[i1]).astype(np.float32)
    kp[..., 2] = np.minimum(clip["kp"][0][i0, :, 2], clip["kp"][0][i1, :, 2])
    human_phase = [human_phase[i] for i in np.round(src).astype(int).clip(0, Th - 1)]
    Th = Tn
  mfile = np.load(a.motion)
  names = [str(x) for x in mfile["clip_names"]]
  starts = {n: int(np.where(mfile["clip_id"] == i)[0][0]) for i, n in enumerate(names)}
  lens = {n: int((mfile["clip_id"] == i).sum()) for i, n in enumerate(names)}
  dance_clip = {0: "bda_zhao_sss", 1: "bda2_gxdsm_full"}
  dance_name = {0: "闪身步", 1: "狗熊哆嗦毛"}
  STAND = {(0, 60.0), (0, 34.0), (1, 5.0), (1, 225.0)}

  env_cfg = load_env_cfg(a.task, play=True)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = 1
  env_cfg.terminations = {}
  old = env_cfg.commands["motion"]
  kw = {f.name: getattr(old, f.name) for f in dataclasses.fields(old) if f.init}
  kw.update(motion_file=a.motion, sampling_mode="start")
  env_cfg.commands["motion"] = PhaseMotionCommandCfg(**kw)
  env = ManagerBasedRlEnv(cfg=env_cfg, device=dev, render_mode="rgb_array" if a.video else None)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  cmd = env.command_manager.get_term("motion")

  def to50(dance, f30):
    c = dance_clip[dance]
    return float(np.clip(starts[c] + f30 * 50 / 30, starts[c], starts[c] + lens[c] - 2))

  if a.mode == "model":
    ws = torch.load(Path.home() / "projects/dance/vla/runs" / a.watch / "model.pt", weights_only=False)
    net = RetrieveNet().to(dev).eval()
    net.load_state_dict(ws["model"])
  else:
    canon_gt, move_gt = align(a.clip)
    cls_gt = to_class(canon_gt, move_gt, TABLE)

  def predict(h):
    if a.mode == "oracle_align":
      k = int(cls_gt[min(h, len(cls_gt) - 1)])
      return k, 1.0
    idx = np.clip(np.arange(h - 29, h + 1), 0, Th - 1)
    with torch.no_grad():
      pr = net(torch.tensor(normalise(kp[idx]).reshape(1, 30, -1), device=dev)).softmax(-1)[0]
    # dance decision = total probability mass per dance; state = best state within that dance
    pd = [float(pr[torch.tensor(STATE_DANCE == d, device=dev)].sum()) for d in (0, 1)]
    d = int(np.argmax(pd))
    masked = pr.clone()
    masked[torch.tensor(STATE_DANCE != d, device=dev)] = 0
    return int(masked.argmax()), pd[d]

  def place_at(p):
    """Write the reference state at global frame p into the sim (used once at start)."""
    T = int(cmd.motion.time_step_total)
    onehot = torch.zeros(T, device=dev)
    onehot[int(p)] = 1
    saved_mode, saved_prior = cmd.cfg.sampling_mode, cmd.frame_prior_eff
    cmd.cfg.sampling_mode, cmd.frame_prior_eff = "uniform", onehot
    cmd._resample_command(torch.arange(1, device=dev))
    cmd.cfg.sampling_mode, cmd.frame_prior_eff = saved_mode, saved_prior

  env.reset()
  k0, _ = predict(0)
  dance = int(STATE_DANCE[k0])
  p, rate = to50(dance, STATE_FRAME[k0]), 0.0
  place_at(p)
  obs = venv.get_observations()

  frames, logs, fell, pending = [], [], None, []
  steps = int(Th / 30 * 50)
  robot_phase, rates = [], []
  for s in range(steps):
    if s % 5 == 0:
      h = min(int(s * env.step_dt * 30), Th - 1)
      k, conf = predict(h)
      pending.append((s + a.latency, k, conf))
    while pending and pending[0][0] <= s:
      _, k, conf = pending.pop(0)
      d, f30 = int(STATE_DANCE[k]), float(STATE_FRAME[k])
      q = to50(d, f30)
      if (d, f30) in STAND:
        p, rate = q, 0.0
      elif d != dance or abs(q - p) > 12:
        p, rate = q, 1.0
      else:
        rate = float(np.clip(1.0 + (q - p) / 10.0, 0.3, 2.0))
      dance = d
      logs.append({"step": s, "dance": d, "dance_p": conf, "phase": CANON_PHASE[dance_name[d]][int(round(f30))]})
    # drive the reference: after the command's internal +1 the time step equals round(p)
    pi = int(round(p))
    cmd.time_steps[:] = pi - 1
    cmd.cur_end[:] = cmd.clip_end[pi]
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
    c = dance_clip[dance]
    robot_phase.append(CANON_PHASE[dance_name[dance]][min(int((pi - starts[c]) * 30 / 50), len(CANON_PHASE[dance_name[dance]]) - 1)])
    p = min(p + rate, starts[c] + lens[c] - 2)
    if robot_phase[-1] not in ("stand", "ready"):
      rates.append(rate)
    z = float(cmd.robot_anchor_pos_w[0, 2])
    qa = cmd.robot_anchor_quat_w[0].cpu().numpy()
    up = Rot.from_quat(np.r_[qa[1:], qa[0]]).apply([0, 0, 1])[2]
    logs.append({"step": s, "track_err": float(cmd.metrics["error_body_pos"][0]), "ref_frame": pi})
    if a.video:
      frames.append(env.render())
    if fell is None and (z < 0.45 or up < 0.5):
      fell = s
      break

  # sync metrics
  n = len(robot_phase)
  hp = [human_phase[min(int(s * 0.02 * 30), Th - 1)] for s in range(n)]
  norm = lambda x: "stand" if x in ("stand", "ready") else x  # noqa: E731
  sync = float(np.mean([norm(r) == norm(h) for r, h in zip(robot_phase, hp)]))
  onset = lambda seq: [i for i in range(1, len(seq)) if seq[i] in ("flash",) and seq[i - 1] != "flash"]  # noqa: E731
  ho, ro = onset(hp), onset(robot_phase)
  lags = [min((r - h for r in ro), key=abs) * 0.02 for h in ho if ro and min(abs(r - h) for r in ro) <= 50]
  te = [l["track_err"] for l in logs if "track_err" in l]
  res = {"clip": a.clip, "mode": a.mode, "watch": a.watch if a.mode == "model" else "-", "latency_steps": a.latency,
         "speed": a.speed, "playback_rate_mean": round(float(np.mean(rates)), 3) if rates else None,
         "steps": steps, "completed": fell is None, "fell_at_s": None if fell is None else round(fell * 0.02, 2),
         "track_err_mean": round(float(np.mean(te)), 4), "phase_sync": round(sync, 3),
         "flash_onsets_human": len(ho), "flash_onsets_matched": len(lags),
         "flash_lag_s_mean": round(float(np.mean(lags)), 3) if lags else None,
         "dance_pred_frac_sss": round(float(np.mean([l["dance"] == 0 for l in logs if "dance" in l])), 3)}
  out = Path.home() / "projects/dance/vla/retrieve_loop"
  out.mkdir(parents=True, exist_ok=True)
  name = (f"{a.clip}_{a.mode}_{res['watch']}_lat{a.latency}" + (f"_x{a.speed}" if a.speed != 1.0 else "")
          + (f"_{a.kp}" if a.kp != "vit" else "") + a.tag)
  res["kp"] = a.kp
  json.dump({"result": res, "log": logs}, open(out / f"{name}.json", "w"))
  if a.video and frames:
    import imageio.v2 as imageio
    imageio.mimsave(out / f"{name}.mp4", frames, fps=50, macro_block_size=1)
  print(json.dumps(res, ensure_ascii=False))
