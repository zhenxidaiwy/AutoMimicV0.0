#!/usr/bin/env bash
# One round of the trigger work: (optional) train an open-set recogniser, then robust_eval (jittered) closed-only and
# closed + open veto. Usage: bash robust_round.sh <open name> [train args...]   (train skipped if the model exists)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
N=$1; shift
L=~/projects/dance_logs
if [ ! -f ~/projects/dance/vla/runs/$N/model.pt ]; then
  cd ~/dance_win/vla && python train_retrieve_open.py --name $N "$@" 2>&1 | grep -v -i warn > $L/train_$N.log
  grep -E "^ep|FINAL|yolo views" $L/train_$N.log
fi
cd ~/dance_win/live
[ -f ~/projects/dance/vla/trigger_eval/robust_ret_lead0_s0_none.json ] || \
  python robust_eval.py 2>&1 | grep -v -i warn > $L/robust_closed.log
head -n 14 $L/robust_closed.log
python robust_eval.py --open $N 2>&1 | grep -v -i warn > $L/robust_$N.log
head -n 22 $L/robust_$N.log
