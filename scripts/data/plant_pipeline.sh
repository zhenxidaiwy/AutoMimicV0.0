#!/usr/bin/env bash
# plant_pipeline.sh <clip>: planted feet level on the floor in the stand phases, legs only (g1_lock_vlm.csv ->
# g1_plant_vlm.csv) -> diff / speed checks -> 50 fps package with held final pose (variant plant_vlm) -> QA vs GVHMR
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1
G=~/projects/dance/data/g1/$id
python feet_plant.py $id --src lock_vlm || exit 1
python stance_check.py $G/g1_plant_vlm.csv 0 5 9 15 69 73 77
python csv_diff.py $G/g1_lock_vlm.csv $G/g1_plant_vlm.csv 4
python ref_speed.py $G/g1_lock_vlm.csv $G/g1_plant_vlm.csv
bash prep_skill.sh $id plant_vlm
bash qa_variant_vs_gvhmr.sh $id g1_plant_vlm
