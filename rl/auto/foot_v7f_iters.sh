#!/usr/bin/env bash
# Stomping / stepping across v7f checkpoints (from falls and from a standing start), plus the v7f reward curve terms.
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7f_n2048 | tail -1)
for it in 19500 20000 20550 21098; do
  CK=$D/model_$it.pt; [ -f $CK ] || continue
  echo "== v7f model_$it, from falls"; bash ~/dance_win/rl/auto/foot_check.sh $CK Dance-Recovery-G1-v7f
  echo "== v7f model_$it, standing start"; bash ~/dance_win/rl/auto/foot_check.sh $CK Dance-Recovery-G1-v7f --stand_start | grep -v "robots that"
done
