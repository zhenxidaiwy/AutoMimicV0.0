#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
python ~/dance_win/rl/test_multi_boundary.py 2>&1 | grep -E "boundary|PASS|FAIL|Error|assert|Traceback|line [0-9]+"
