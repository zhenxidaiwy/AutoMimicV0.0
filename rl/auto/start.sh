#!/usr/bin/env bash
# Start the self-iterating harness after the v7f chain, warm-starting from the v7f run.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
while pgrep -f chain_getup_v7f.sh > /dev/null; do sleep 30; done
WARM=$(basename $(ls -d $R/*_getup_v7f_n2048 | tail -1))
cd ~/dance_win/rl/auto && exec ~/miniforge3/envs/gmr/bin/python -u harness.py --warm $WARM --rounds ${1:-10} --iters ${2:-1500}
