#!/usr/bin/env bash
# Get-up sim2sim, all phases (see native_getup.py docstring). Usage:
#   bash native_getup.sh            # full run: 64 initial states x 10 s, then native, then report + video
#   bash native_getup.sh quick      # smoke test: 8 states x 60 steps, no video
# Logs: ~/dance_win/sim2sim/out/getup_run.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
mkdir -p out
LOG=out/getup_run.log
if [ "$1" = "quick" ]; then ARGS="--n 8 --steps 60"; VID="--no_video"; else ARGS="--n 64 --steps 500"; VID=""; fi
{
  python native_getup.py mjlab $ARGS || exit 1
  python native_getup.py native || exit 1
  python native_getup.py report $VID || exit 1
} 2>&1 | grep -v -E "^Module |Warp [0-9]|CUDA Toolkit|Devices:|\"cuda:0\"|\"cpu\"|Kernel cache|^\s*$" > $LOG
tail -c 20000 $LOG
