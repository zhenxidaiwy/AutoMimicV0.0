#!/usr/bin/env bash
# ground_hands_check.sh <clip>: labels -> ground fix with hand contacts (root height only) -> foot lock -> checks
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1
python write_annotation.py $id || exit 1
python ground_fix.py $id --contacts vlm --hands --sigma 2 || exit 1
python foot_lock.py $id --contacts vlm || exit 1
G=~/projects/dance/data/g1/$id
python hand_floor.py $G/g1_lock_vlm.csv 2
python ref_speed.py $G/g1.csv $G/g1_lock_vlm.csv
