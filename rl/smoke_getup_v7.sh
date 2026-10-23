#!/usr/bin/env bash
# Smoke test v7 + baseline template distance of the v6c policy (what v7 must improve).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=Dance-Recovery-G1-v7
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name v7smoke \
  --agent.logger tensorboard --agent.resume True --agent.load-run 2026-10-19_18-35-45_getup_v6c_n2048 \
  > ~/projects/dance_logs/smoke_getup_v7.log 2>&1
echo "exit=$?"
grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/smoke_getup_v7.log | head -8
grep -E "Episode_Reward/(stand_template|upright|stand_up)" ~/projects/dance_logs/smoke_getup_v7.log | tail -3
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*v7smoke
echo "== baseline: v6c model_9850 stance vs template"
bash ~/dance_win/rl/stance_check.sh ~/projects/dance/runs/logs/rsl_rl/g1_recovery/2026-10-19_18-35-45_getup_v6c_n2048/model_9850.pt
