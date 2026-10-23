#!/usr/bin/env bash
# mark_aborted.sh K: rename the log / run dir of a round that was started and stopped (so a new round K does not mix)
K=$(printf %02d $1)
mv ~/projects/dance_logs/train_flipauto_r$K.log ~/projects/dance_logs/train_flipauto_r${K}_aborted_rules.log 2>/dev/null
for d in ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_flipauto_r$K; do
  [ -d "$d" ] && mv "$d" "${d}_aborted_rules" && echo "moved $d"
done
ls ~/projects/dance_logs | grep "r$K"
