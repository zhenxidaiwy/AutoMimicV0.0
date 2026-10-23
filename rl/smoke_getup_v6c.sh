#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=Dance-Recovery-G1-v6c
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name v6csmoke \
  --agent.logger tensorboard --agent.resume True --agent.load-run 2026-10-19_17-15-09_getup_v6b_n2048 \
  > ~/projects/dance_logs/smoke_getup_v6c.log 2>&1
echo "exit=$?"
grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v6c.log | head -8
grep -E "Episode_Reward/(upright|stand_up|waist_bend|stance|standing_posture|feet_planted)" ~/projects/dance_logs/smoke_getup_v6c.log | tail -6
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*v6csmoke
