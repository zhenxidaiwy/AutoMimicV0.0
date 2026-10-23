#!/usr/bin/env bash
# Everything the VLM annotator needs for one clip: full-body crop sheet (every 3 frames) + 2D ankle speed table.
# Usage: bash annot_prep.sh <clip_id> [step=3]
P=~/miniforge3/envs/gmr/bin/python; id=$1; st=${2:-3}
$P ~/dance_win/scripts/data/crop_sheet.py $id --step $st --cols 14 --h 170
$P ~/dance_win/scripts/data/ankle2d.py $id --step 2 > ~/dance_win/data/qa/$id/ankle2d.txt
echo "ankle table: ~/dance_win/data/qa/$id/ankle2d.txt"
