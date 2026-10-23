"""Check that no env ever steps across a clip boundary in the multi-motion command (and that every clip is visited)."""
import sys
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(Path(__file__).resolve().parent))

if __name__ == "__main__":
  import dataclasses

  import torch
  import mjlab.tasks  # noqa: F401
  import src.tasks  # noqa: F401
  from mjlab.envs import ManagerBasedRlEnv
  from mjlab.tasks.registry import load_env_cfg
  from phase_rsi import PhaseMotionCommandCfg

  M = str(Path.home() / "projects/dance/multi/train_v1.npz")
  cfg = load_env_cfg("Unitree-G1-Tracking-No-State-Estimation")
  cfg.scene.num_envs = 256
  old = cfg.commands["motion"]
  kw = {f.name: getattr(old, f.name) for f in dataclasses.fields(old) if f.init}
  kw.update(motion_file=M, frame_weight_file=M.replace(".npz", "_prior.npz"), sampling_mode="uniform")
  cfg.commands["motion"] = PhaseMotionCommandCfg(**kw)
  env = ManagerBasedRlEnv(cfg=cfg, device="cuda:0")
  env.reset()
  cmd = env.command_manager.get_term("motion")
  act = torch.zeros(env.num_envs, env.action_manager.total_action_dim, device="cuda:0")
  prev_t, prev_cid = cmd.time_steps.clone(), cmd.clip_id[cmd.time_steps].clone()
  bad, visited, transitions = 0, set(), 0
  for step in range(400):
    env.step(act)
    t = cmd.time_steps
    cid = cmd.clip_id[t]
    visited |= set(cid.tolist())
    # an env either advanced by exactly 1 within the same clip, or was resampled (any jump) -> a jump across a
    # boundary without resampling would show up as t == prev_t + 1 with a different clip id
    crossed = (t == prev_t + 1) & (cid != prev_cid)
    bad += int(crossed.sum())
    transitions += int((t != prev_t + 1).sum())
    assert bool((t < cmd.cur_end).all()), "time_step beyond its clip end"
    assert bool((t >= cmd.clip_start[cmd.cur_end - 1]).all()), "cur_end does not belong to current clip"
    prev_t, prev_cid = t.clone(), cid.clone()
  print(f"boundary crossings without resample: {bad}; resamples/jumps seen: {transitions}; "
        f"clips visited: {sorted(visited)} of {len(cmd.clip_names)}")
  print("PASS" if bad == 0 and len(visited) == len(cmd.clip_names) else "FAIL")
