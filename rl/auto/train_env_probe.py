"""Run a fixed policy (no learning) in the TRAINING config (stand / squat starts, pushes, randomisation) and report,
per start kind, the fraction of robots with pelvis > 0.65 m over time, plus the per-step reward terms averaged over
the rollout. Tells whether a training collapse comes from the environment/reward or from learning dynamics.
Usage (unitree_rl_mjlab env): GETUP_TASK=... GETUP_KNOBS=... python train_env_probe.py --ckpt <model.pt>
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
  ap.add_argument("--n", type=int, default=512)
  ap.add_argument("--seconds", type=float, default=10.0)
  ap.add_argument("--stochastic", action="store_true", help="sample actions like training (policy noise std)")
  a = ap.parse_args()
  import torch
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=False)
  cfg.scene.num_envs = a.n
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  if a.stochastic:
    actor = runner.alg.actor
    policy = lambda o: actor(o, stochastic_output=True)  # noqa: E731
    p = [v for k, v in actor.state_dict().items() if "std" in k.lower()]
    print("policy noise std param:", [round(float(x.mean()), 3) for x in p])
  robot = env.scene["robot"]
  rm = env.reward_manager
  env.episode_length_buf[:] = 0  # no random initial episode clock: every env starts a fresh episode
  env.reset()
  obs = venv.get_observations()
  kind = env._getup_kind.clone()
  names = rm.active_terms if hasattr(rm, "active_terms") else list(rm._term_names)
  sums = {nm: 0.0 for nm in names}
  steps = int(a.seconds / env.step_dt)
  for s in range(steps):
    with torch.no_grad():
      obs, rew, done, _ = venv.step(policy(obs))
    if hasattr(rm, "_step_reward"):
      for i, nm in enumerate(names):
        sums[nm] += float(rm._step_reward[:, i].mean())
    t = (s + 1) * env.step_dt
    if abs(t - round(t)) < 1e-6 and round(t) in (1, 2, 3, 4, 6, 8, 10):
      z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
      up = z > 0.65
      parts = []
      for k, nm in ((0, "lying"), (2, "squat"), (1, "stand")):
        m = kind == k
        if m.any():
          parts.append(f"{nm} {up[m].float().mean():.0%} (n={int(m.sum())})")
      print(f"t={t:4.1f}s pelvis>0.65 m: " + ", ".join(parts) + f"   resets so far: {int(done.sum())}")
  print("mean per-step reward terms over the rollout (x dt already applied by the manager):")
  for nm in names:
    print(f"  {nm:<20} {sums[nm] / steps:+.4f}")
