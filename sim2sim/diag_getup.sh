#!/usr/bin/env bash
# Physics-difference diagnostic (see diag_getup.py). Full log: out/getup_diag.log, summary: out/getup_diag.json
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim && mkdir -p out && python diag_getup.py > out/getup_diag.log 2>&1
grep -E "^\[|^=====|^   env|^euler|^elliptic|Error|Traceback|line [0-9]+" out/getup_diag.log | grep -v "^\[INFO" | cut -c 1-400
