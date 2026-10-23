"""Train the G1 get-up policy (task Dance-Recovery-G1) with unitree_rl_mjlab's train.py machinery.
Usage (unitree_rl_mjlab env): python train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations 1000 ...
Logs: ~/projects/dance/runs/logs/rsl_rl/g1_recovery/<time>_<run-name>/
"""
import importlib.util
import os
import sys
from pathlib import Path

REPO = Path.home() / "projects" / "unitree_rl_mjlab"
HERE = Path(__file__).resolve().parent

if __name__ == "__main__":
  rest = sys.argv[1:]
  if rest and rest[0] == "--":
    rest = rest[1:]
  sys.path.insert(0, str(REPO))
  sys.path.insert(0, str(HERE))
  import wandb
  _S = wandb.Settings
  wandb.Settings = lambda *a, **kw: _S(*a, **{k: v for k, v in kw.items() if k != "start_method"})
  import mjlab
  import mjlab.tasks  # noqa: F401
  import tyro
  from getup import TASK_ID

  if os.environ.get("GETUP_NO_RANDOM_EP_LEN") == "1":
    # The get-up rewards depend on the episode clock (rise schedule, time gates), which the policy does not observe;
    # randomising the initial episode lengths (rsl_rl default when training starts) puts lying robots at t = 3-10 s
    # and gives the critic unpredictable returns right after a warm start.
    from rsl_rl.runners import OnPolicyRunner
    _learn = OnPolicyRunner.learn
    OnPolicyRunner.learn = lambda self, num_learning_iterations, init_at_random_ep_len=False: \
        _learn(self, num_learning_iterations, init_at_random_ep_len=False)

  spec = importlib.util.spec_from_file_location("ur_train", REPO / "scripts" / "train.py")
  T = importlib.util.module_from_spec(spec)
  sys.modules["ur_train"] = T
  spec.loader.exec_module(T)
  args = tyro.cli(T.TrainConfig, args=rest, default=T.TrainConfig.from_task(TASK_ID), config=mjlab.TYRO_FLAGS)
  run_root = Path.home() / "projects" / "dance" / "runs"
  os.chdir(run_root)
  T.launch_training(task_id=TASK_ID, args=args)
