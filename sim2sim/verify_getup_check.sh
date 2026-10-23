#!/usr/bin/env bash
# Adversarial verifier for the get-up sim2sim. Usage: bash verify_getup_check.sh [check|closed|replay|all]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
mkdir -p verify_getup_out
PH=${1:-all}
FILTER="^Module |Warp [0-9]|CUDA Toolkit|Devices:|\"cuda:0\"|\"cpu\"|Kernel cache|^\s*$"
if [ "$PH" = "check" ] || [ "$PH" = "all" ]; then
  python verify_getup_check.py check 2>&1 | grep -v -E "$FILTER" > verify_getup_out/check.log
  tail -c 9000 verify_getup_out/check.log
fi
if [ "$PH" = "closed" ] || [ "$PH" = "all" ]; then
  python verify_getup_check.py closed 2>&1 | grep -v -E "$FILTER" > verify_getup_out/closed.log
  tail -c 9000 verify_getup_out/closed.log
fi
if [ "$PH" = "replay" ] || [ "$PH" = "all" ]; then
  python verify_getup_check.py replay 2>&1 | grep -v -E "$FILTER" > verify_getup_out/replay.log
  tail -c 9000 verify_getup_out/replay.log
fi
