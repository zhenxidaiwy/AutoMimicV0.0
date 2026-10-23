#!/usr/bin/env bash
# Usage: bash foot_check.sh <ckpt> <task> [--stand_start]
GETUP_TASK=$2 bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/foot_check.py --ckpt $1 ${@:3} 2>&1 | \
  grep -E "robots that|touchdowns|travel|in the air|force|Error|Traceback|line [0-9]+,"
