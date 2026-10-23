#!/usr/bin/env bash
# Squat RSI check on the latest checkpoint of the current harness round.
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_auto_r* | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
GETUP_TASK=Dance-Recovery-G1-auto bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/squat_rsi_check.py \
  --ckpt $CK 2>&1 | grep -E "^t=|Error|Traceback|line [0-9]+,"
