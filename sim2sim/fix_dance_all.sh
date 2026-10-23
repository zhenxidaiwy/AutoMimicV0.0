#!/usr/bin/env bash
# FIX stage: re-run the full dance sim2sim (mjlab + native cross-version + report) after the metric/report fixes.
source ~/miniforge3/etc/profile.d/conda.sh
conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
mkdir -p logs
python -m py_compile native_dance.py || exit 1
echo "[compile ok]"
bash native_dance.sh all > logs/fix_dance_all.log 2>&1
echo "[exit $?]"
tail -n 40 logs/fix_dance_all.log
