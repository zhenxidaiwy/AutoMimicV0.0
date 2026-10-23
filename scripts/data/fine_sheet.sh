#!/usr/bin/env bash
# Fine contact sheet for one time window of a raw video.
# Usage: bash fine_sheet.sh <raw_id> <start_s> <end_s> [every_s=0.25] [tile_w=200]
P=~/miniforge3/envs/gmr/bin/python
$P ~/dance_win/scripts/data/sheet.py ~/projects/dance/data/raw/$1.mp4 ~/dance_win/data/qa/sheets/$1_${2}_${3}.png \
  --start $2 --end $3 --every ${4:-0.25} --cols 10 --w ${5:-200} --max_tiles 60
