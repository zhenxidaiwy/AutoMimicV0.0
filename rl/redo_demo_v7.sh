#!/usr/bin/env bash
# Re-render the v7 2x2 demo (the chain's demo step failed on the reset 'pose' kwarg) and package the policy.
export GETUP_TASK=Dance-Recovery-G1-v7
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7_final "G1 get-up v7 (canonical standing template)"
ls -la ~/dance_win/videos/getup/getup_v7_final.mp4
ls ~/dance_win/policies/getup_v7/
