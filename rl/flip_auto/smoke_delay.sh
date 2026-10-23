#!/usr/bin/env bash
# smoke_delay.sh: 2-iteration training with --delay-ms 25 to check the DelayedActuator wrapping
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
DS=~/projects/dance/dataset/backflip_3
cd ~/dance_win/rl/flip_auto && python quant_report.py 14 | sed -n '/## A2/,/## B/p'
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --flip-rewards 2 --knee-limit 120 --delay-ms 25 \
  -- --motion-file $DS/g1_ballistic_50fps.npz --env.scene.num-envs 128 --agent.max-iterations 2 \
  --agent.run-name smoke_delay --agent.logger tensorboard 2>&1 | grep -E "delay|knee|Traceback|Error|Learning iteration 1/" | cut -c 1-300
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_smoke_delay
