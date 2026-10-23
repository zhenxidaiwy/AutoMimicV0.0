#!/usr/bin/env bash
# High-level model: with vs without VLM auxiliary heads, 3 seeds each.
for s in 0 1 2; do
  bash ~/dance_win/vla/train_watch.sh v1_aux_s$s --seed $s | grep FINAL
  bash ~/dance_win/vla/train_watch.sh v1_noaux_s$s --seed $s --no_aux | grep FINAL
done
echo RUN_V1_DONE
