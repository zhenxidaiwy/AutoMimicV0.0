#!/usr/bin/env bash
# Fine contact sheets + cut detection for held-out candidates in ~/projects/dance/data/raw_unseen.
# Usage: bash unseen_fine.sh "<aid> <start> <end> [every] [w] [cols]" ["..." ...]   (one quoted spec per sheet)
#        bash unseen_fine.sh cuts <aid> [<aid> ...]
P=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_unseen; SH=~/dance_win/scripts/data/tmp_sheets; mkdir -p $SH
if [ "$1" = "cuts" ]; then
  shift
  for aid in "$@"; do $P -I ~/dance_win/scripts/data/unseen_cuts.py $RAW/av$aid.mp4; done
  exit 0
fi
for spec in "$@"; do
  set -- $spec
  $P -I ~/dance_win/scripts/data/sheet.py $RAW/av$1.mp4 $SH/av$1_$2_$3.png \
    --start $2 --end $3 --every ${4:-0.25} --w ${5:-200} --cols ${6:-10} --max_tiles 80
done
