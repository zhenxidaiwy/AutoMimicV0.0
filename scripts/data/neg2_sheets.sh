#!/usr/bin/env bash
# Overview sheets (1 s) + cut detection for already-downloaded batch-2 candidates (skips existing sheets).
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_neg2; SH=~/dance_win/scripts/data/tmp_sheets_neg2; mkdir -p $SH
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 10 --w 128 --max_tiles 80
  $PY -I ~/dance_win/scripts/data/unseen_cuts.py $v
done
