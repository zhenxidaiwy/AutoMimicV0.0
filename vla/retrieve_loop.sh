#!/usr/bin/env bash
# Usage: bash retrieve_loop.sh <clip> <watch_run> <tracker_ckpt> [extra args]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
clip=$1; w=$2; ck=$3; shift 3
python ~/dance_win/vla/retrieve_loop.py --clip $clip --watch $w --ckpt $ck "$@" 2>&1 | grep -E '^\{|Error|Traceback|line [0-9]+,'
