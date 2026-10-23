#!/usr/bin/env bash
# Fine sheets for positive-training candidates in ~/projects/dance/data/raw_pos_train.
# Usage: bash pos_fine.sh "<aid> <start> <end> [every] [w] [cols]" ...
P=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_pos_train; SH=~/dance_win/scripts/data/tmp_sheets_pos; mkdir -p $SH
for spec in "$@"; do
  set -- $spec
  $P -I ~/dance_win/scripts/data/sheet.py $RAW/av$1.mp4 $SH/av$1_$2_$3.png \
    --start $2 --end $3 --every ${4:-0.5} --w ${5:-110} --cols ${6:-10} --max_tiles 80
done
