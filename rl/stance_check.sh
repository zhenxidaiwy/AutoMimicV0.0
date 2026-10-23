#!/usr/bin/env bash
# Usage: GETUP_TASK=<task> bash stance_check.sh <ckpt>
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
python ~/dance_win/rl/stance_check.py --ckpt $1 2>&1 | grep -E "standing|tilt|height|feet|stance|drift|template|shoulders|dist|^joint|Error|Traceback|line [0-9]+,"
