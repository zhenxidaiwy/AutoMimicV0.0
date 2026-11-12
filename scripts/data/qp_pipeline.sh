#!/usr/bin/env bash
# qp_pipeline.sh <clip> [qp weight]: hand+foot grounding with a SMOOTH root offset (bounded least squares, no
# penetration, penalised vertical acceleration) -> foot lock -> feet plant in the stand phases -> 50 fps package with
# held final pose (variant plantqp_vlm) -> checks (root z / acceleration, hands, speed) -> QA render vs GVHMR
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1; W=${2:-30}
G=~/projects/dance/data/g1/$id
python ground_fix.py $id --contacts vlm --hands --src g1_palm --qp $W --out groundqp | head -c 900; echo
python foot_lock.py $id --contacts vlm --src groundqp --out lockqp | head -c 300; echo
python feet_plant.py $id --src lockqp_vlm --out plantqp_vlm | head -c 600; echo
python root_z_compare.py $id 24 50 g1 g1_plant_vlm g1_plantqp_vlm
python hand_floor.py $G/g1_plantqp_vlm.csv 2 | sed -n '1p;15,27p'
python ref_speed.py $G/g1_plant_vlm.csv $G/g1_plantqp_vlm.csv
bash prep_skill.sh $id plantqp_vlm
bash qa_variant_vs_gvhmr.sh $id g1_plantqp_vlm
