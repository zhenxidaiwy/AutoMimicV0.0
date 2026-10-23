#!/usr/bin/env bash
# All episode reward / termination terms at the last logged iteration of harness rounds. Usage: bash terms_round.sh 2 3
for k in "$@"; do
  L=~/projects/dance_logs/auto/r$(printf "%02d" $k)/train.log
  n=$(grep -an "Learning iteration" $L | tail -3 | head -1 | cut -d: -f1)
  echo "== round $k (from line $n)"
  tail -n +$n $L | grep -aE "Learning iteration|Episode_Reward|Episode_Termination|Mean reward|Mean episode length" | head -40
done
