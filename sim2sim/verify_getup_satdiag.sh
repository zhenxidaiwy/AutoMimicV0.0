#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
mkdir -p verify_getup_out
python verify_getup_satdiag.py > verify_getup_out/satdiag.log 2>&1
grep -E "^\[(nominal|euler|no force|satdiag)|Error|Traceback|line [0-9]+" verify_getup_out/satdiag.log | cut -c 1-400
