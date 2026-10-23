#!/usr/bin/env bash
# Does the round-5 policy (100% get-up when measured at 14:2x) still stand up under the CURRENT code?
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
CK=$(ls -d $R/*_auto_r05)/model_23499.pt
T=~/projects/dance_logs/auto_selftest; mkdir -p $T
GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=~/projects/dance_logs/auto/r05/knobs.json \
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $T/r5now.json > $T/r5now.log 2>&1
echo "exit=$?"
grep -E "Traceback|Error" $T/r5now.log | head -3
grep -E "\"success\"|t_stand_median|sway_pp" $T/r5now.json | head -4
echo "== round 5 at the time:"; grep -E "\"success\"|t_stand_median" ~/projects/dance_logs/auto/r05/fall.json | head -2
