#!/usr/bin/env bash
# Usage: GETUP_TASK=<task> bash smooth_check.sh <ckpt>
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=${GETUP_TASK:-Dance-Recovery-G1-v7c}
python ~/dance_win/rl/smooth_check.py --ckpt $1 ${@:2} 2>&1 | grep -E "peak|transient|time with|worst|^  [a-z_]+_joint|Error|Traceback|line [0-9]+,"
