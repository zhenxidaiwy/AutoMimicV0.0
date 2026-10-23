#!/usr/bin/env bash
# Latest get-up run dir and its checkpoints.
d=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/* | tail -1)
echo "latest run: $(basename $d)"
ls $d | grep -E "^model_" | sort -V | tail -3
grep -E "Learning iteration" ~/projects/dance_logs/train_getup_n2048.log | tail -1
