#!/usr/bin/env bash
# Evaluate the finished first run (iter 2500), then continue it to 5000 iterations, then evaluate again.
FIRST=2026-10-19_11-28-36_getup_n2048
D=~/projects/dance/runs/logs/rsl_rl/g1_recovery/$FIRST
echo "[resume_5000] eval of $FIRST/model_2499 $(date)"
CKPT=$D/model_2499.pt bash ~/dance_win/rl/eval_getup.sh --video
echo "[resume_5000] resuming $(date)"
RESUME=$FIRST bash ~/dance_win/rl/train_getup.sh 2048 2500
echo "[resume_5000] finished $(date)"
R=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_n2048_resume | tail -1)
CKPT=$(ls $R/model_*.pt | sort -V | tail -1) bash ~/dance_win/rl/eval_getup.sh --video
