#!/usr/bin/env bash
# Fix stage: report phase of the get-up sim2sim (results_getup.json/.md + video), then dump a few video frames to
# out/fix_frames/. Log: out/fix_getup_report.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim || exit 1
python native_getup.py report > out/fix_getup_report.log 2>&1 || { tail -n 30 out/fix_getup_report.log; exit 1; }
grep -E "^video:" out/fix_getup_report.log
python fix_getup_frames.py
ls -la --time-style=+%H:%M:%S results_getup.md results_getup.json ../videos/sim2sim/getup_side_by_side.mp4
