#!/usr/bin/env bash
# Generalisation test of the user's pick (v7f model_19500): stats for 9 initial conditions + 3x3 video.
CK=~/dance_win/policies/getup_v7f_19500/policy.pt
OUT=~/dance_win/videos/getup/getup_v7f_19500_generalization.mp4
GETUP_TASK=Dance-Recovery-G1-v7f bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/gen_test.py \
  --ckpt $CK --out $OUT --video 2>&1 | grep -vE "^\||Warning|warn|^\s*$|GaussianDistribution|─|━"
