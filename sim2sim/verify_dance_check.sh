#!/usr/bin/env bash
# Adversarial dance sim2sim verifier. Usage: bash verify_dance_check.sh   (both clips)
source ~/miniforge3/etc/profile.d/conda.sh
conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/sim2sim
mkdir -p logs
for c in sss gxdsm; do
  python verify_dance_check.py --clip "$c" > logs/verify_dance_$c.log 2>&1
  grep -E "^\[|Error|Traceback|line [0-9]+," logs/verify_dance_$c.log
done
