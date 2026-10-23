#!/usr/bin/env bash
# Quick eval of the stopped v7d run (time-to-stand per pose) before v7e continues from it.
export GETUP_TASK=Dance-Recovery-G1-v7d
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7d_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
CKPT=$CK RUN_FILTER=_getup_v7d_n2048 bash ~/dance_win/rl/eval_getup.sh | grep -E "max pelvis|overall|supine|face-down|side"
