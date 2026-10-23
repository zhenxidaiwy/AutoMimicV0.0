#!/usr/bin/env bash
# Round-5 policy in the training config (round-5 knobs), deterministic vs sampled actions; also round-4 sampled.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
probe() { GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=~/projects/dance_logs/auto/$2/knobs.json \
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/train_env_probe.py --ckpt $1 --n 256 ${@:3} 2>&1 | \
  grep -E "^t=|noise std|Error|Traceback|line [0-9]+,"; }
echo "== r5 model_23499, sampled actions"; probe $(ls -d $R/*_auto_r05)/model_23499.pt r05 --stochastic
echo "== r5 model_23000, sampled actions"; probe $(ls -d $R/*_auto_r05)/model_23000.pt r05 --stochastic
echo "== r4 model_22000, sampled actions"; probe $(ls -d $R/*_auto_r04)/model_22000.pt r04 --stochastic
