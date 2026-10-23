#!/usr/bin/env bash
# dev probe for native_getup.py (see probe_getup.py)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim && python probe_getup.py 2>&1 | grep -v -E "Warp|^Module" | head -c 30000
