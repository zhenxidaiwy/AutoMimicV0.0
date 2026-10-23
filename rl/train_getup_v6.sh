#!/usr/bin/env bash
# Train the v6 (slow, realistic) get-up policy. Usage: bash train_getup_v6.sh [num_envs=2048] [iters=2500]
# RESUME=<run dir name> continues from that run's latest checkpoint. Log: ~/projects/dance_logs/train_getup_v6*.log
# (Separate file from train_getup.sh on purpose: never edit a script while it runs.)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off GETUP_TASK=Dance-Recovery-G1-v6
N=${1:-2048}; IT=${2:-2500}; run=getup_v6_n${N}${RESUME:+_resume}
extra=(--agent.logger wandb --agent.wandb-project g1_dance)
grep -qE "api.wandb.ai|forge.coreweave.com" ~/.netrc 2>/dev/null || extra=(--agent.logger tensorboard)
[ -n "$RESUME" ] && extra+=(--agent.resume True --agent.load-run "$RESUME")
mkdir -p ~/projects/dance_logs
echo "[train_getup_v6] $(date) run=$run task=$GETUP_TASK" | tee ~/projects/dance_logs/train_$run.log
python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs $N --agent.max-iterations $IT \
  --agent.run-name $run "${extra[@]}" >> ~/projects/dance_logs/train_$run.log 2>&1
echo "[train_getup_v6] exit=$? $(date)" | tee -a ~/projects/dance_logs/train_$run.log
