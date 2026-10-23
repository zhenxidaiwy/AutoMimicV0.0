#!/usr/bin/env bash
# Saturation x implicitfast diagnostic + push capability test (see diag_getup_sat.py). Log: out/getup_satdiag.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
python diag_getup_sat.py > out/getup_satdiag.log 2>&1
grep -E "^\[sat\]|Error|Traceback|line [0-9]+" out/getup_satdiag.log | cut -c 1-400
ls -la --time-style=+%H:%M:%S out/getup_diag.json out/getup_satdiag.json
