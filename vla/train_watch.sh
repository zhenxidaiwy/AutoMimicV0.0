#!/usr/bin/env bash
# Usage: bash train_watch.sh <name> [extra args for train_watch.py]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
mkdir -p ~/projects/dance_logs
name=$1; shift
python ~/dance_win/vla/train_watch.py --name $name "$@" 2>&1 | grep -vE "Warning|warn" | tee ~/projects/dance_logs/watch_$name.log | grep -E "^train|^ep|FINAL|Error|Traceback|line [0-9]+,"
