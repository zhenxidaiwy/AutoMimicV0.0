#!/usr/bin/env bash
# Feet close-up sheets (every 2 frames) for given windows of a clip.
# Usage: bash feet_sheets.sh <clip_id> <s1> <e1> [<s2> <e2> ...]
P=~/miniforge3/envs/gmr/bin/python; id=$1; shift
while [ $# -ge 2 ]; do
  $P ~/dance_win/scripts/data/crop_sheet.py $id --lower --step 2 --cols 12 --h 150 --start $1 --end $2
  shift 2
done
