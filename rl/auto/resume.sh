#!/usr/bin/env bash
# Resume the self-iterating get-up harness from ~/projects/dance_logs/auto/state.json (stopped with park.sh).
# Usage: bash resume.sh [rounds=10] [iters=1500]
cd ~/dance_win/rl/auto && exec ~/miniforge3/envs/gmr/bin/python -u harness.py --warm unused --rounds ${1:-10} --iters ${2:-1500}
