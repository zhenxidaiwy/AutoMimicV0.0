#!/usr/bin/env bash
# Clean up the accidental fresh run (caused by editing train_getup.sh while it was executing) and restart the
# 2500 -> 5000 continuation from the real first run.
pkill -f chain_getup.sh
pkill -f "rl/train_getup.sh 2048 2500"
pkill -f "train_getup.py"
sleep 5
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_recovery/2026-10-19_12-24-41_getup_n2048
pgrep -fa "train_getup|chain_getup" || echo "clean: no get-up processes"
ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/* | tail -2
