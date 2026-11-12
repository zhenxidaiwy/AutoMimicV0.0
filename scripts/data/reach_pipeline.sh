#!/usr/bin/env bash
# reach_pipeline.sh <clip>: arm-only reach of the planted hands on the smooth-root reference (g1_plantqp_vlm.csv ->
# g1_reachqp_vlm.csv) -> diff / speed checks -> 50 fps package with held final pose (variant reachqp_vlm) -> QA vs GVHMR
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1
G=~/projects/dance/data/g1/$id
python arm_reach.py $id --src plantqp_vlm --out reachqp_vlm | head -c 700; echo
python csv_diff.py $G/g1_plant_vlm.csv $G/g1_reachqp_vlm.csv 2 | sed -n '1p;12,28p;$p'
python ref_speed.py $G/g1_plant_vlm.csv $G/g1_reachqp_vlm.csv
bash prep_skill.sh $id reachqp_vlm | tail -3
bash qa_variant_vs_gvhmr.sh $id g1_reachqp_vlm
cd ~/dance_win && bash scripts/data/grab_frames.sh data/qa/$id/qa_g1_reachqp_vlm_vs_gvhmr.mp4 data/qa/$id/reach_check.jpg 0.95 1.1 1.25 1.4 1.55
