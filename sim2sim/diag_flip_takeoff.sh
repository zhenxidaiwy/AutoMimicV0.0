#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl
cd ~/dance_win/sim2sim && python diag_flip_takeoff.py --policy ${1:-backflip_r14_fid2} 2>&1 | grep -vE "Warning|warn\(|INFO|^\s*$" | tee logs/flip_takeoffdiag.log
