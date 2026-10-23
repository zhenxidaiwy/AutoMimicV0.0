"""Can the get-up policy stay standing if the waist roll/pitch targets are forced to 0 (straight torso)?
Phase 1: policy as is for 6 s (gets up). Phase 2: same policy, but waist_roll/pitch actions replaced by the value
that commands 0 rad, for 6 s. Reports standing count and tilts at the end of each phase.
Usage (unitree_rl_mjlab env): GETUP_TASK=... python waist_override_test.py --ckpt <model.pt>
"""
import argparse
import sys
from dataclasses import asdict
from pathlib import Path

sys.path.insert(0, str(Path.home() / "projects" / "unitree_rl_mjlab"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--ckpt", required=True)
  ap.add_argument("--n", type=int, default=64)
  a = ap.parse_args()
  import torch
  import mjlab.tasks  # noqa: F401
  from getup import TASK_ID
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.rl import MjlabOnPolicyRunner, RslRlVecEnvWrapper
  from mjlab.tasks.registry import load_env_cfg, load_rl_cfg, load_runner_cls
  from mjlab.utils.lab_api.math import quat_apply_inverse

  dev = "cuda:0"
  cfg = load_env_cfg(TASK_ID, play=True)
  cfg.scene.num_envs = a.n
  env = ManagerBasedRlEnv(cfg=cfg, device=dev)
  agent = load_rl_cfg(TASK_ID)
  venv = RslRlVecEnvWrapper(env, clip_actions=agent.clip_actions)
  runner = (load_runner_cls(TASK_ID) or MjlabOnPolicyRunner)(venv, asdict(agent), device=dev)
  runner.load(a.ckpt, load_cfg={"actor": True}, strict=True, map_location=dev)
  policy = runner.get_inference_policy(device=dev)
  robot = env.scene["robot"]
  term = env.action_manager.get_term("joint_pos")
  tnames = list(term._target_names)
  widx = [tnames.index("waist_roll_joint"), tnames.index("waist_pitch_joint")]
  off = term.offset if isinstance(term.offset, float) else term.offset[0, widx]
  sc = term.scale if isinstance(term.scale, float) else term.scale[0, widx]
  zero_raw = (0.0 - off) / sc  # raw action that commands 0 rad
  jn = list(robot.joint_names)
  jw = [jn.index("waist_roll_joint"), jn.index("waist_pitch_joint")]
  ti = list(robot.body_names).index("torso_link")
  g = torch.tensor([0.0, 0.0, -1.0], device=dev).repeat(a.n, 1)

  def report(tag):
    z = robot.data.root_link_pos_w[:, 2] - env.scene.env_origins[:, 2]
    tor = torch.rad2deg(torch.acos(torch.clamp(-quat_apply_inverse(robot.data.body_link_quat_w[:, ti], g)[:, 2], -1, 1)))
    pel = torch.rad2deg(torch.acos(torch.clamp(-robot.data.projected_gravity_b[:, 2], -1, 1)))
    st = z > 0.6
    print(f"{tag}: standing {int(st.sum())}/{a.n} | torso tilt median {tor[st].median():.1f} deg | pelvis tilt "
          f"{pel[st].median():.1f} deg | waist roll/pitch {robot.data.joint_pos[st][:, jw].median(0).values.tolist()}")

  env.reset()
  obs = venv.get_observations()
  for _ in range(300):
    with torch.no_grad():
      obs, _, _, _ = venv.step(policy(obs))
  report("phase 1 (policy as is, 6 s)")
  for _ in range(300):
    with torch.no_grad():
      act = policy(obs)
      act[:, widx] = zero_raw
      obs, _, _, _ = venv.step(act)
  report("phase 2 (waist forced to 0, +6 s)")
