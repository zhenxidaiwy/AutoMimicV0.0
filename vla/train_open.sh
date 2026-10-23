#!/usr/bin/env bash
# Open-set recogniser training, then the offline trigger evaluation with it.
# Usage: bash train_open.sh <name> [train_retrieve_open.py args...]   Log: ~/projects/dance_logs/train_<name>.log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
N=$1; shift
cd ~/dance_win/vla || exit 1
LOG=~/projects/dance_logs/train_$N.log
python train_retrieve_open.py --name $N "$@" 2>&1 | grep -v -i warn > $LOG || exit 1
grep -E "^ep|FINAL|AIST" $LOG
cd ~/dance_win/live && python trigger_eval.py --watch $N 2>&1 | grep -v -i warn > ~/projects/dance_logs/trigger_eval_$N.log
python rank_rules.py $N | head -n 8
python other_stats.py $N
python combo_eval.py ret_lead0_s0 $N 2>&1 | grep -v -i warn | head -n 12
