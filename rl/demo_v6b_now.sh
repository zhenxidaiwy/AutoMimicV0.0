#!/usr/bin/env bash
# 2x2 demo of the current latest v6b checkpoint (playback only).
export GETUP_TASK=Dance-Recovery-G1-v6b
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v6b_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1)
name=getup_v6b_$(basename ${CK%.pt} | sed 's/model_/iter/')
bash ~/dance_win/rl/demo_getup.sh $CK $name "G1 get-up v6b ($(basename ${CK%.pt})): slow & realistic reward, training in progress"
