#!/usr/bin/env bash
# Stomping / stepping: v7f final vs harness round 0, from falls and from a standing start.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
V7F=$(ls $(ls -d $R/*_getup_v7f_n2048 | tail -1)/model_*.pt | sort -V | tail -1)
R0=$(ls $(ls -d $R/*_auto_r00 | tail -1)/model_*.pt | sort -V | tail -1)
echo "== v7f final, from falls"; bash ~/dance_win/rl/auto/foot_check.sh $V7F Dance-Recovery-G1-v7f
echo "== v7f final, standing start"; bash ~/dance_win/rl/auto/foot_check.sh $V7F Dance-Recovery-G1-v7f --stand_start
echo "== auto r00, from falls"; bash ~/dance_win/rl/auto/foot_check.sh $R0 Dance-Recovery-G1-auto
