#!/usr/bin/env bash
# DIAGNOSTIC backflip run: same as train_run.sh (phase RSI, ee threshold 0.6) with actuator effort limits scaled.
# Usage: bash train_flip_diag.sh <clip> <variant> <effort_scale> [iters=1000]   Log: dance_logs/train_<run>.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
clip=$1; var=$2; es=$3; IT=${4:-1000}
DS=~/projects/dance/dataset/$clip
run=${clip}_${var}_phase_effort${es}_n4096
echo "[diag] $(date) run=$run" | tee ~/projects/dance_logs/train_$run.log
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --ee-threshold 0.6 --effort-scale $es -- \
  --motion-file $DS/g1_${var}_50fps.npz --env.scene.num-envs 4096 --agent.max-iterations $IT \
  --agent.run-name $run --agent.logger tensorboard >> ~/projects/dance_logs/train_$run.log 2>&1
echo "[diag] exit=$? $(date)" | tee -a ~/projects/dance_logs/train_$run.log
EFFORT=$es bash ~/dance_win/rl/eval_flip.sh $run $clip $var
