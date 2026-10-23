#!/usr/bin/env bash
# Baseline + anticipation variants, 3 seeds each:
#   shadow   : W=1, H=1 (frame-wise, no temporal context, no anticipation) -- HumanPlus-style
#   lead5    : chunked model trained to anticipate 5 robot steps (100 ms latency compensation)
for s in 0 1 2; do
  bash ~/dance_win/vla/train_watch.sh shadow_s$s --seed $s --W 1 --H 1 | grep FINAL
  bash ~/dance_win/vla/train_watch.sh lead5_s$s --seed $s --lead 5 | grep FINAL
done
echo RUN_V2_DONE
