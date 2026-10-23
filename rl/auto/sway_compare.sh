#!/usr/bin/env bash
# Upper-body sway after standing: round 4 (selected), round 2, v7f 19500.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
run() { GETUP_TASK=$2 bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/sway_check.py --ckpt $1 ${@:3} 2>&1 | \
  grep -E "robots analysed|torso|sway|joints moving|Error|Traceback|line [0-9]+,"; }
echo "== round 4 model_22000, from falls"; run $(ls -d $R/*_auto_r04)/model_22000.pt Dance-Recovery-G1-auto
echo "== round 4 model_22000, standing start"; run $(ls -d $R/*_auto_r04)/model_22000.pt Dance-Recovery-G1-auto --stand_start
echo "== round 2 model_20999, from falls"; run $(ls -d $R/*_auto_r02)/model_20999.pt Dance-Recovery-G1-auto
echo "== v7f model_19500, from falls"; run ~/dance_win/policies/getup_v7f_19500/policy.pt Dance-Recovery-G1-v7f
