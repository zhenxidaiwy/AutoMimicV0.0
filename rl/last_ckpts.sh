#!/usr/bin/env bash
d=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/* | tail -1)
ls --time-style=+%H:%M:%S -la $d/model_*.pt | sort -V -k7 | tail -3
ls -d ~/projects/dance/runs/wandb/run-* 2>/dev/null | tail -1
