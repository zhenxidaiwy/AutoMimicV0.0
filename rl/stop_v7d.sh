#!/usr/bin/env bash
# Stop the v7d chain (bash wrapper first so it does not go on to eval/demo/package a half-trained run), then training.
pkill -f chain_getup_v7d.sh; sleep 1
pkill -f train_getup.py; sleep 5
pgrep -fa "chain_getup|train_getup" || echo "stopped"
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7d_n2048 | tail -1)
ls $D/model_*.pt | sort -V | tail -1
