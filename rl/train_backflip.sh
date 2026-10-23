#!/usr/bin/env bash
# Backflip capability probe: specialist tracker per (clip, variant), one after the other (1000 iters each).
# Usage: bash train_backflip.sh backflip_2:lock_vlm backflip_2:ballistic ...
for spec in "$@"; do
  IFS=: read -r clip var <<< "$spec"
  echo "=== $clip $var $(date +%T)"
  LOGGER=tensorboard RSI=${RSI:-phase} EXTRA="$EXTRA" bash ~/dance_win/rl/train_run.sh $clip ${RSI:-phase} 4096 1000 $var
  tail -n 3 ~/projects/dance_logs/train_${clip}_${var}_${RSI:-phase}_n4096.log
done
echo ALL_DONE
