#!/usr/bin/env bash
# Round 8 just started with the knobs the round-7 watchdog relaxed: stop it, restore round-5 values, smoke-free restart.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
for d in $R/*_auto_r08; do [ -d "$d" ] && rm -rf "$d" && echo "removed $d"; done
rm -rf $A/r08
bash ~/dance_win/rl/auto/restore_r5_knobs.sh > /dev/null
bash ~/dance_win/rl/auto/show_state.sh | tail -3
