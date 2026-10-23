#!/usr/bin/env bash
# Leg spread while rising, latest v7e checkpoint.
export GETUP_TASK=Dance-Recovery-G1-v7e
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7e_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
bash ~/dance_win/rl/smooth_check.sh $CK --skip 0.1 | grep -E "feet|peak joint speed"
