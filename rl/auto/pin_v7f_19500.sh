#!/usr/bin/env bash
# User's pick (2026-10-20): v7f model_19500 looks best. Package it, and tell the harness to continue from it.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
D=$(ls -d $R/*_getup_v7f_n2048 | tail -1)
P=~/dance_win/policies/getup_v7f_19500; mkdir -p $P
cp $D/model_19500.pt $P/policy.pt; cp $D/params/*.yaml $P/ 2>/dev/null
cp ~/dance_win/videos/getup/getup_v7f_iter19500.mp4 $P/demo.mp4
echo "source: $D/model_19500.pt (task Dance-Recovery-G1-v7f) - chosen by the user as the best-looking get-up" > $P/SOURCE.txt
ls -la $P
mkdir -p ~/projects/dance_logs/auto
printf '{"warm": "%s", "warm_ckpt": "model_19500.pt", "reason": "user pick: v7f model_19500 looks best"}\n' \
  "$(basename $D)" > ~/projects/dance_logs/auto/override_warm.json
cat ~/projects/dance_logs/auto/override_warm.json
