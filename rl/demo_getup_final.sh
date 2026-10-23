#!/usr/bin/env bash
# Final get-up policy: package it next to the dance policies and render the 2x2 demo (playback only, no training).
d=~/projects/dance/runs/logs/rsl_rl/g1_recovery/2026-10-19_12-29-06_getup_n2048_resume
ck=$(ls $d/model_*.pt | sort -V | tail -1)
echo "final checkpoint: $ck"
mkdir -p ~/dance_win/policies/getup_v5
cp $ck ~/dance_win/policies/getup_v5/policy.pt
cp $d/*.onnx ~/dance_win/policies/getup_v5/ 2>/dev/null
cp $d/params/*.yaml ~/dance_win/policies/getup_v5/ 2>/dev/null
echo "source: $ck (task Dance-Recovery-G1, reward v5 = signed upright; adapted from chaoticcuriosity-io/g1-humanoid-rl, MIT)" \
  > ~/dance_win/policies/getup_v5/SOURCE.txt
bash ~/dance_win/rl/demo_getup.sh $ck getup_final "G1 get-up policy (final, iter 5000): 4 fallen poses"
