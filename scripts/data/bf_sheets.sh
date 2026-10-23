#!/usr/bin/env bash
# Overview sheets + cut detection for already-downloaded backflip candidates (skips existing sheets and .part files).
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_backflip; SH=~/dance_win/scripts/data/tmp_sheets_bf; mkdir -p $SH
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 0.5 --cols 10 --w 160 --max_tiles 80
  $PY -I ~/dance_win/scripts/data/unseen_cuts.py $v
done
