#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/sim2sim && python diag_flip_solver.py --policy ${1:-backflip_r14_fid2} 2>&1 | grep -vE "Warning|warn\("
