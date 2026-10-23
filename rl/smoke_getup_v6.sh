#!/usr/bin/env bash
# 5-iteration smoke test of v6 (tensorboard), print reward terms, then remove the smoke run dir.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=Dance-Recovery-G1-v6
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 5 --agent.run-name v6smoke \
  --agent.logger tensorboard > ~/projects/dance_logs/smoke_getup_v6.log 2>&1
echo "exit=$?"
grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v6.log | head -8
grep -E "Learning iteration 4/|Episode_Reward/" ~/projects/dance_logs/smoke_getup_v6.log | tail -16
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*v6smoke
