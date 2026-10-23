#!/usr/bin/env bash
# Export the backflip env model (knee limit 120 N.m) -> models/flip.mjb / flip.xml / flip_info.json / flip_fields.npz
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim && mkdir -p logs && python export_flip_model.py "$@" 2>&1 | grep -vE "Warning|warn\(" | tee logs/export_flip.log | grep -E "^\[|^   |Error|Traceback|line [0-9]+,"
ls -la ~/dance_win/sim2sim/models/ | grep flip
