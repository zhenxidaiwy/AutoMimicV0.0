#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
python fix_getup_satnames.py 2>&1 | tail -n 60
