#!/usr/bin/env bash
# RL smoke test: phase-aware RSI on the BDA reference clip, small env count, few iterations; reports throughput + VRAM.
# Usage: bash smoke.sh [num_envs=1024] [iters=30] [rsi=phase_adaptive]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
DS=~/projects/dance/dataset/bda_zhao_sss
N=${1:-1024}; IT=${2:-30}; RSI=${3:-phase_adaptive}
( while true; do nvidia-smi --query-gpu=memory.used --format=csv,noheader,nounits >> /tmp/smoke_vram.txt; sleep 2; done ) &
MON=$!
: > /tmp/smoke_vram.txt
start=$(date +%s)
python ~/dance_win/rl/train_dance.py --rsi $RSI --labels $DS/labels_50fps.npz -- \
  --motion-file $DS/g1_lock_vlm_50fps.npz --env.scene.num-envs $N --agent.max-iterations $IT \
  --agent.run-name smoke_${RSI}_n$N --agent.logger tensorboard 2>&1 | grep -vE "Warning|warn" | tail -40
end=$(date +%s); kill $MON
echo "wall ${N} envs x ${IT} iters: $((end-start)) s ; peak VRAM MiB: $(sort -n /tmp/smoke_vram.txt | tail -1)"
