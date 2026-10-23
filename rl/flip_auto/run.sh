#!/usr/bin/env bash
# Start / resume the backflip auto harness. Log: ~/projects/dance_logs/flip_auto.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
python harness.py "$@" >> ~/projects/dance_logs/flip_auto.log 2>&1
