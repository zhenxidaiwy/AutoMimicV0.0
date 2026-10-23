#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/live && python compat_probe.py 2>&1 | grep -E "^==|^   |same joint|tracking:|getup:|default pose|action scale|Error|Traceback|line [0-9]+,"
