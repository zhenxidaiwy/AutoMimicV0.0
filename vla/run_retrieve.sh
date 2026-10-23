#!/usr/bin/env bash
# Skill-retrieval high level, 3 seeds; lead 0 and lead 3 (100 ms anticipation at 30 fps).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
for s in 0 1 2; do
  for L in 0 3; do
    python ~/dance_win/vla/train_retrieve.py --name ret_lead${L}_s$s --seed $s --lead $L 2>&1 | grep -E "^ep|FINAL|Error|Traceback|line [0-9]+,"
  done
done
echo RUN_RETRIEVE_DONE
