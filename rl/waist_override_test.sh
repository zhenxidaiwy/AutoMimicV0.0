#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=Dance-Recovery-G1-v6c
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v6c_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
python ~/dance_win/rl/waist_override_test.py --ckpt $CK 2>&1 | grep -E "phase|Error|Traceback|line [0-9]+,"
