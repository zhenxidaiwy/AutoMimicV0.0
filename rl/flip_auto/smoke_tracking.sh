#!/usr/bin/env bash
# 2-iteration smoke run of the fidelity curriculum flags
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
DS=~/projects/dance/dataset/backflip_3
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --flip-rewards 2 \
  --tracking-scale 1.5 --tracking-std-scale 0.85 --knee-limit 120 -- --motion-file $DS/g1_ballistic_50fps.npz \
  --env.scene.num-envs 128 --agent.max-iterations 2 --agent.run-name smoke_tracking --agent.logger tensorboard 2>&1 \
  | grep -E "fidelity|flip_root_pos|Traceback|Error|Learning iteration 1/" | cut -c 1-200
