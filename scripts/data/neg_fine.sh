#!/usr/bin/env bash
# Cut detection + fine sheets for negative candidates in ~/projects/dance/data/raw_neg.
# Usage: bash neg_fine.sh cuts <aid> ...   |   bash neg_fine.sh "<aid> <start> <end> [every] [w] [cols]" ...
P=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_neg; SH=~/dance_win/scripts/data/tmp_sheets_neg; mkdir -p $SH
if [ "$1" = "cuts" ]; then
  shift
  for aid in "$@"; do $P -I ~/dance_win/scripts/data/unseen_cuts.py $RAW/av$aid.mp4; done
  exit 0
fi
for spec in "$@"; do
  set -- $spec
  $P -I ~/dance_win/scripts/data/sheet.py $RAW/av$1.mp4 $SH/av$1_$2_$3.png \
    --start $2 --end $3 --every ${4:-0.5} --w ${5:-200} --cols ${6:-10} --max_tiles 80
done
