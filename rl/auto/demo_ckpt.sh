#!/usr/bin/env bash
# 2x2 demo video of a specific checkpoint. Usage: bash demo_ckpt.sh <run dir glob suffix> <iteration> <task> <name>
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
D=$(ls -d $R/*_$1 | tail -1)
GETUP_TASK=$3 bash ~/dance_win/rl/demo_getup.sh $D/model_$2.pt $4 "G1 get-up $1 iter $2"
