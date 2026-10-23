#!/usr/bin/env bash
# Offline trigger-rule comparison (keypoints first: kp_live_tests.py on Windows, dancecam env).
# Log: ~/projects/dance_logs/trigger_eval.log
source ~/miniforge3/etc/profile.d/conda.sh
cd ~/dance_win/live || exit 1
mkdir -p ~/projects/dance_logs
LOG=~/projects/dance_logs/trigger_eval.log
{
  conda activate unitree_rl_mjlab
  python trigger_eval.py "$@"
} > $LOG 2>&1
grep -v -E "Warning|warn" $LOG | tail -n 80
