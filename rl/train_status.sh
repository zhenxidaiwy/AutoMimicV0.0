#!/usr/bin/env bash
# Progress of a training log: header, latest iteration, key metrics. Usage: bash train_status.sh <run>
L=~/projects/dance_logs/train_$1.log
head -2 $L
grep -E "Learning iteration" $L | tail -1
for k in "Mean reward" "Mean episode length" "error_body_pos" "error_anchor_pos" "Episode_Termination/ee_body_pos" "Episode_Termination/anchor_ori" "Iteration time" "Time elapsed" "ETA"; do
  grep -E "$k" $L | tail -1
done
nvidia-smi --query-gpu=memory.used,utilization.gpu,power.draw --format=csv,noheader
