#!/usr/bin/env bash
# Full training run on one dataset clip. Log: ~/projects/dance_logs/train_<run>.log
# Usage: bash train_run.sh <clip_id> <rsi: uniform|adaptive|phase|phase_adaptive> [num_envs=4096] [iters=1000] [variant=lock_vlm]
# 1000 iterations is the default (user decision 2026-10-18: the clip converges by ~750-1000 iters, ~45 min).
# Resume: add RESUME=<run dir name> in the environment (loads its last checkpoint).
# Logger: LOGGER=wandb (default if ~/.netrc has a W&B key, project "g1_dance") or LOGGER=tensorboard.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export WANDB_CONSOLE=off  # console upload made W&B lag far behind training
clip=$1; rsi=$2; N=${3:-4096}; IT=${4:-1000}; var=${5:-lock_vlm}
DS=~/projects/dance/dataset/$clip
run=${clip}_${var}_${rsi}_n${N}
extra=()
[ -n "$RESUME" ] && extra=(--agent.resume True --agent.load-run "$RESUME")
if [ -z "$LOGGER" ]; then grep -qE "api.wandb.ai|forge.coreweave.com" ~/.netrc 2>/dev/null && LOGGER=wandb || LOGGER=tensorboard; fi
[ "$LOGGER" = wandb ] && extra+=(--agent.wandb-project g1_dance)
mkdir -p ~/projects/dance_logs
echo "[train_run] $(date) run=$run motion=$DS/g1_${var}_50fps.npz" | tee ~/projects/dance_logs/train_$run.log
nvidia-smi --query-gpu=name,memory.used,power.draw,power.limit --format=csv,noheader | tee -a ~/projects/dance_logs/train_$run.log
python ~/dance_win/rl/train_dance.py --rsi $rsi --labels $DS/labels_50fps.npz $EXTRA -- \
  --motion-file $DS/g1_${var}_50fps.npz --env.scene.num-envs $N --agent.max-iterations $IT \
  --agent.run-name $run --agent.logger $LOGGER "${extra[@]}" >> ~/projects/dance_logs/train_$run.log 2>&1
echo "[train_run] exit=$? $(date)" | tee -a ~/projects/dance_logs/train_$run.log
