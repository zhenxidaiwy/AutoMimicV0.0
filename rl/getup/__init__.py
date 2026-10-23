"""G1 get-up (fall recovery) tasks for mjlab 1.2.0.

Adapted from chaoticcuriosity-io/g1-humanoid-rl (MIT license), recovery-task/ at commit 2c7e7fe:
https://github.com/chaoticcuriosity-io/g1-humanoid-rl/tree/main/recovery-task
Dance-Recovery-G1    : v5 reward (signed upright; fixes the upside-down hack of the original v4)
Dance-Recovery-G1-v6 : v6 reward (slow, no flight / launching, standing posture, both feet planted)
GETUP_TASK env var selects the task in train_getup.py / eval_getup.py / demo_getup.py (default v5).
"""
import os

from mjlab.tasks.registry import register_mjlab_task
from mjlab.tasks.velocity.rl import VelocityOnPolicyRunner

from .env_cfg import (unitree_g1_recovery_env_cfg, unitree_g1_recovery_ppo_runner_cfg, unitree_g1_recovery_v6_env_cfg,
                      unitree_g1_recovery_v6b_env_cfg, unitree_g1_recovery_v6c_env_cfg, unitree_g1_recovery_v7_env_cfg,
                      unitree_g1_recovery_v7b_env_cfg, unitree_g1_recovery_v7c_env_cfg,
                      unitree_g1_recovery_v7d_env_cfg, unitree_g1_recovery_v7e_env_cfg,
                      unitree_g1_recovery_v7f_env_cfg, unitree_g1_recovery_v8_env_cfg,
                      unitree_g1_recovery_auto_env_cfg)

register_mjlab_task(
  task_id="Dance-Recovery-G1",
  env_cfg=unitree_g1_recovery_env_cfg(),
  play_env_cfg=unitree_g1_recovery_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)
register_mjlab_task(
  task_id="Dance-Recovery-G1-v6",
  env_cfg=unitree_g1_recovery_v6_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v6_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v6b",
  env_cfg=unitree_g1_recovery_v6b_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v6b_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v6c",
  env_cfg=unitree_g1_recovery_v6c_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v6c_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7",
  env_cfg=unitree_g1_recovery_v7_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7b",
  env_cfg=unitree_g1_recovery_v7b_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7b_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7c",
  env_cfg=unitree_g1_recovery_v7c_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7c_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7d",
  env_cfg=unitree_g1_recovery_v7d_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7d_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7e",
  env_cfg=unitree_g1_recovery_v7e_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7e_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v7f",
  env_cfg=unitree_g1_recovery_v7f_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v7f_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

register_mjlab_task(
  task_id="Dance-Recovery-G1-v8",
  env_cfg=unitree_g1_recovery_v8_env_cfg(),
  play_env_cfg=unitree_g1_recovery_v8_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

# self-iterating harness task: reward knobs from the JSON in $GETUP_KNOBS (see rl/auto/harness.py)
register_mjlab_task(
  task_id="Dance-Recovery-G1-auto",
  env_cfg=unitree_g1_recovery_auto_env_cfg(),
  play_env_cfg=unitree_g1_recovery_auto_env_cfg(play=True),
  rl_cfg=unitree_g1_recovery_ppo_runner_cfg(),
  runner_cls=VelocityOnPolicyRunner,
)

TASK_ID = os.environ.get("GETUP_TASK", "Dance-Recovery-G1")
