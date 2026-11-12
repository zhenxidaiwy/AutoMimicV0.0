#!/usr/bin/env bash
# palm_pipeline.sh <clip>: palm-down wrists on planted hands -> ground fix with hands (root height only) -> foot lock
# -> checks + QA comparison with the GVHMR render
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1
G=~/projects/dance/data/g1/$id
python wrist_flat.py $id --src g1 || exit 1
python ground_fix.py $id --contacts vlm --hands --sigma 2 --src g1_palm | head -c 400; echo
python foot_lock.py $id --contacts vlm | head -c 300; echo
python hand_floor.py $G/g1_lock_vlm.csv 2 | sed -n '1p;15,27p'
python ref_speed.py $G/g1.csv $G/g1_lock_vlm.csv
bash qa_variant_vs_gvhmr.sh $id g1_lock_vlm
bash grab_frames.sh ~/dance_win/data/qa/$id/qa_g1_lock_vlm.mp4 ~/dance_win/videos/candidates/${id}_palm_big.jpg 1.0 1.2 1.3 1.45
