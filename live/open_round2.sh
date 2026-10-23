#!/usr/bin/env bash
# Open-set veto with real negatives (batch 1) in training; evaluated on held-out batch 2 + positives.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
L=~/projects/dance_logs; RN=neg_1,neg_2,neg_3,neg_4,neg_5,neg_6,neg_7,neg_8,neg_9
cd ~/dance_win/vla
[ -f ~/projects/dance/vla/runs/open_s3/model.pt ] || python train_retrieve_open.py --name open_s3 --yolo_views 8 --real_neg $RN 2>&1 | grep -v -i warn > $L/train_open_s3.log
[ -f ~/projects/dance/vla/runs/open_s4/model.pt ] || python train_retrieve_open.py --name open_s4 --real_neg $RN --real_neg_frac 0.6 2>&1 | grep -v -i warn > $L/train_open_s4.log
grep -h -E "FINAL" $L/train_open_s3.log $L/train_open_s4.log
cd ~/dance_win/live
for N in open_s0 open_s3 open_s4; do
  python heldout_eval.py $N 10 0.5 0.7 0.9 2>&1 | grep -A3 -E "^(old|vote)"
done
