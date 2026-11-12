"""World-model data: roll a saved tracking checkpoint out in mjlab and log the robot transitions (SuperMimic idea:
the dynamics do not depend on the policy that collected them, so every past checkpoint of every skill is data).
Per step: the full robot state, the executed (noisy, delayed) action and the reference frame. The sim context xi is
fixed per run and known: foot friction, PD stiffness scale, per-env action delay (0..max steps). No pushes, no CoM /
encoder randomisation: a deterministic model conditioned on xi (pushes can be injected later as a root-velocity edit
of the state in imagination).
Usage (unitree_rl_mjlab env): python collect.py --ckpt <model.pt> --motion <clip.npz> --out <file.npz>
  [--envs 512] [--steps 1000] [--noise 0.1] [--friction 1.0] [--kp-scale 1.0] [--max-delay 2]
  [--hand-friction 0.6] [--knee-limit 120]"""
import argparse
import dataclasses
import json
import sys
from dataclasses import asdict
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"


def run(a):
  import numpy as np
  import torch
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
  env_cfg = load_env_cfg(a.task)
  agent_cfg = load_rl_cfg(a.task)
  env_cfg.scene.num_envs = a.envs
  tracking = "motion" in env_cfg.commands
  # the same tracked bodies for every task (get-up has no reference: names taken from the tracking task)
  body_names = (env_cfg.commands["motion"] if tracking else
                load_env_cfg("Unitree-G1-Tracking-No-State-Estimation").commands["motion"]).body_names
  if tracking:
    cmd_cfg = env_cfg.commands["motion"]
    cmd_cfg.motion_file = str(Path(a.motion).resolve())
    cmd_cfg.sampling_mode = "uniform"  # starts all over the clip: every phase is covered
  for k in ("push_robot", "base_com", "encoder_bias"):
    env_cfg.events.pop(k, None)
  # long windows for the model: z-only tracking terminations at the hand-support training value (0.6 m), not 0.25
  for k in ("anchor_pos", "ee_body_pos"):
    if env_cfg.terminations.get(k) is not None and "threshold" in env_cfg.terminations[k].params:
      p = env_cfg.terminations[k].params
      p["threshold"] = max(p["threshold"], 0.6)
  if "foot_friction" in env_cfg.events:
    ev = env_cfg.events["foot_friction"]
    for key in ev.params:
      if "range" in key:
        ev.params[key] = (a.friction, a.friction)
  art = env_cfg.scene.entities["robot"].articulation
  if a.knee_limit is not None:
    from flip_rewards import set_knee_limit
    set_knee_limit(art, a.knee_limit)
  if a.hand_friction > 0:
    from mimic_generic import set_hand_friction
    set_hand_friction(env_cfg.scene.entities["robot"], a.hand_friction)
  if a.kp_scale != 1.0:
    art.actuators = tuple(dataclasses.replace(c, stiffness=c.stiffness * a.kp_scale) for c in art.actuators)
  env = ManagerBasedRlEnv(cfg=env_cfg, device="cuda:0")
  venv = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
  runner = (load_runner_cls(a.task) or MjlabOnPolicyRunner)(venv, asdict(agent_cfg), device="cuda:0")
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location="cuda:0")
  policy = runner.get_inference_policy(device="cuda:0")
  cmd = env.command_manager.get_term("motion") if tracking else None
  robot = env.scene["robot"]
  d = robot.data
  bidx = robot.find_bodies(body_names, preserve_order=True)[0]
  N = a.envs
  g = torch.Generator(device="cuda:0").manual_seed(a.seed)
  delay = torch.randint(0, a.max_delay + 1, (N,), device="cuda:0", generator=g)
  env.reset()
  obs = venv.get_observations()
  with torch.no_grad():  # warm-up: the first step after reset() reports done for every env (stale pre-reset state)
    obs, _, _, _ = venv.step(policy(obs))
  hist = None  # (max_delay + 1, N, A): hist[0] = newest command
  rec = {k: [] for k in ("root_pos", "root_quat", "root_lin_vel", "root_ang_vel", "joint_pos", "joint_vel",
                         "body_pos", "body_quat", "action", "command", "frame", "done")}
  ar = torch.arange(N, device="cuda:0")
  for _ in range(a.steps):
    with torch.no_grad():
      act = policy(obs)
      act = act + a.noise * torch.randn(act.shape, device=act.device, generator=g)
    hist = act.unsqueeze(0).repeat(a.max_delay + 1, 1, 1) if hist is None else torch.cat([act[None], hist[:-1]])
    use = hist[delay, ar]
    rec["root_pos"].append((d.root_link_pos_w - env.scene.env_origins).cpu())
    rec["root_quat"].append(d.root_link_quat_w.cpu())
    rec["root_lin_vel"].append(d.root_link_lin_vel_w.cpu())
    rec["root_ang_vel"].append(d.root_link_ang_vel_w.cpu())
    rec["joint_pos"].append(d.joint_pos.cpu())
    rec["joint_vel"].append(d.joint_vel.cpu())
    rec["body_pos"].append((d.body_link_pos_w[:, bidx] - env.scene.env_origins[:, None]).cpu())
    rec["body_quat"].append(d.body_link_quat_w[:, bidx].cpu())
    rec["command"].append(act.cpu())
    rec["action"].append(use.cpu())
    rec["frame"].append(cmd.time_steps.clone().cpu() if tracking else torch.full((N,), -1))
    obs, _, dones, _ = venv.step(use)
    rec["done"].append(dones.bool().cpu())
    if dones.any():  # a reset env starts with an empty command history
      hist[:, dones.bool()] = 0.0
  out = {k: torch.stack(v).numpy() for k, v in rec.items()}  # (T, N, ...)
  for k in out:
    if out[k].dtype == np.float32:
      out[k] = out[k].astype(np.float16) if k not in ("root_pos",) else out[k]
  xi = {"friction": a.friction, "kp_scale": a.kp_scale, "hand_friction": a.hand_friction,
        "knee_limit": a.knee_limit, "noise": a.noise, "ckpt": a.ckpt, "motion": a.motion, "task": a.task,
        "body_names": list(body_names), "joint_names": list(robot.joint_names),
        "terminations": {k: v.params.get("threshold") for k, v in env_cfg.terminations.items() if v is not None}}
  np.savez_compressed(a.out, delay=delay.cpu().numpy(), xi=json.dumps(xi), **out)
  env.close()
  falls = float(out["done"].mean()) * a.steps
  print(json.dumps({"out": a.out, "transitions": int(a.steps * N), "resets_per_env": round(falls, 2)}), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--motion", default="", help="reference clip (tracking tasks only)")
  ap.add_argument("--out", required=True)
  ap.add_argument("--task", default="Unitree-G1-Tracking-No-State-Estimation")
  ap.add_argument("--envs", type=int, default=512)
  ap.add_argument("--steps", type=int, default=1000)
  ap.add_argument("--noise", type=float, default=0.1, help="action noise std (SuperMimic: N(0, 0.1^2))")
  ap.add_argument("--friction", type=float, default=1.0)
  ap.add_argument("--kp-scale", type=float, default=1.0)
  ap.add_argument("--max-delay", type=int, default=2, help="per-env command delay 0..max control steps (20 ms each)")
  ap.add_argument("--hand-friction", type=float, default=0.0)
  ap.add_argument("--knee-limit", type=float, default=120.0)
  ap.add_argument("--seed", type=int, default=0)
  a = ap.parse_args()
  sys.path.insert(0, str(REPO))
  sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  import getup  # noqa: F401  (registers the Dance-Recovery-G1-* get-up tasks)
  run(a)
