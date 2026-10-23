#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
mkdir -p logs
python verify_dance_contacts.py > logs/verify_dance_contacts.log 2>&1
grep -E "^(sss|gxdsm) |Error|Traceback|line [0-9]+," logs/verify_dance_contacts.log
