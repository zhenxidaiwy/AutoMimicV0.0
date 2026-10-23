#!/usr/bin/env bash
# 5-iteration smoke run with the flip terminations (checks they load and fire without errors)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
DS=~/projects/dance/dataset/backflip_3
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --flip-rewards 2 \
  --flip-terms '{"term_flight_spread": {"max_d": 0.6}, "term_hip_extended": {"max_hip": 1.2}, "term_stand_fail": {"max_d": 0.5, "max_tilt": 35.0}}' \
  --knee-limit 120 -- --motion-file $DS/g1_ballistic_50fps.npz --env.scene.num-envs 256 --agent.max-iterations 5 \
  --agent.run-name smoke_terms --agent.logger tensorboard 2>&1 | grep -E "flip terminations|term_|Traceback|Error|Learning iteration 4/" | cut -c 1-200
