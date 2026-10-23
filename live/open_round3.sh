#!/usr/bin/env bash
# Veto recogniser with real negatives (batch 1) AND extra dancers (data/pos_train, POS_ANY) -> held-out evaluation.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
L=~/projects/dance_logs; RN=neg_1,neg_2,neg_3,neg_4,neg_5,neg_6,neg_7,neg_8,neg_9
cd ~/dance_win/vla
for spec in "open_s5 --yolo_views 8 --pos_any 0.3" "open_s6 --yolo_views 8 --pos_any 0.6"; do
  set -- $spec; N=$1; shift
  [ -f ~/projects/dance/vla/runs/$N/model.pt ] || \
    python train_retrieve_open.py --name $N --real_neg $RN "$@" 2>&1 | grep -v -i warn > $L/train_$N.log
  grep -E "FINAL|extra dancers" $L/train_$N.log
done
cd ~/dance_win/live
for N in open_s5 open_s6; do python heldout_eval.py $N 10 0.5 0.7 0.9 2>&1 | grep -A3 -E "^vote"; done
