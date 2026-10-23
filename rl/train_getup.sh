#!/usr/bin/env bash
# Usage: bash train_getup.sh [num_envs=2048] [iters=1000]   (LOGGER=tensorboard to skip W&B)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
# Do not upload the console log to W&B: rsl_rl prints ~40 lines/iteration (67k lines per run), which made the W&B
# upload lag ~400 iterations behind training. Curves/metrics are still logged.
export WANDB_CONSOLE=off
N=${1:-2048}; IT=${2:-1000}; run=getup_n${N}${RESUME:+_resume}
# RESUME=<run dir name under logs/rsl_rl/g1_recovery>: continue from its latest checkpoint for IT more iterations
if [ -z "$LOGGER" ]; then grep -qE "api.wandb.ai|forge.coreweave.com" ~/.netrc 2>/dev/null && LOGGER=wandb || LOGGER=tensorboard; fi
extra=(); [ "$LOGGER" = wandb ] && extra+=(--agent.wandb-project g1_dance)
[ -n "$RESUME" ] && extra+=(--agent.resume True --agent.load-run "$RESUME")
mkdir -p ~/projects/dance_logs
echo "[train_getup] $(date) run=$run" | tee ~/projects/dance_logs/train_$run.log
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs $N --agent.max-iterations $IT \
  --agent.run-name $run --agent.logger $LOGGER "${extra[@]}" >> ~/projects/dance_logs/train_$run.log 2>&1
echo "[train_getup] exit=$? $(date)" | tee -a ~/projects/dance_logs/train_$run.log
