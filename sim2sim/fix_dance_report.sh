#!/usr/bin/env bash
# FIX stage: regenerate results_dance.md/.json from the per-clip JSONs, then probe the regenerated videos.
source ~/miniforge3/etc/profile.d/conda.sh
conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
python native_dance.py --mode report > logs/dance_report.log 2>&1
echo "[report exit $?]"
grep -n "counts:" results_dance.md
python fix_video_probe.py
