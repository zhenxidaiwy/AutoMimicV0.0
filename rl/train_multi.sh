#!/usr/bin/env bash
# Train the generalist (multi-motion) tracker. Log: ~/projects/dance_logs/train_<run>.log
# Usage: bash train_multi.sh <multi_name=train_v1> [rsi=adaptive] [num_envs=4096] [iters=1000]
# Resume: RESUME=<run dir name>.  Logger: LOGGER=wandb|tensorboard (default wandb if logged in).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
export WANDB_CONSOLE=off  # console upload made W&B lag far behind training
name=${1:-train_v1}; rsi=${2:-adaptive}; N=${3:-4096}; IT=${4:-1000}
M=~/projects/dance/multi/$name.npz
run=multi_${name}_${rsi}_n${N}
extra=()
[ -n "$RESUME" ] && extra=(--agent.resume True --agent.load-run "$RESUME")
if [ -z "$LOGGER" ]; then grep -qE "api.wandb.ai|forge.coreweave.com" ~/.netrc 2>/dev/null && LOGGER=wandb || LOGGER=tensorboard; fi
[ "$LOGGER" = wandb ] && extra+=(--agent.wandb-project g1_dance)
mkdir -p ~/projects/dance_logs
echo "[train_multi] $(date) run=$run motion=$M" | tee ~/projects/dance_logs/train_$run.log
python ~/dance_win/rl/train_dance.py --rsi $rsi --prior ${M%.npz}_prior.npz -- \
  --motion-file $M --env.scene.num-envs $N --agent.max-iterations $IT \
  --agent.run-name $run --agent.logger $LOGGER "${extra[@]}" >> ~/projects/dance_logs/train_$run.log 2>&1
echo "[train_multi] exit=$? $(date)" | tee -a ~/projects/dance_logs/train_$run.log
