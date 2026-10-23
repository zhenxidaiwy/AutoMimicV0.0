#!/usr/bin/env bash
# Window-mean 'other' veto with each open-set recogniser (closed-set recogniser for dance / frame).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/live
for N in "$@"; do
  python robust_eval.py --open $N 2>&1 | grep -v -i warn > ~/projects/dance_logs/robust_om_$N.log
  echo "== $N"; head -n 16 ~/projects/dance_logs/robust_om_$N.log | tail -n 13
done
