#!/usr/bin/env bash
# 2x2 demo video of the latest v7e checkpoint -> videos/getup/getup_v7e_iter<N>.mp4
export GETUP_TASK=Dance-Recovery-G1-v7e
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7e_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); it=$(basename $CK .pt | sed 's/model_//')
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7e_iter$it "G1 get-up v7e iter $it (smooth 2-3.5 s get-up)"
