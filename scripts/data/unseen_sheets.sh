#!/usr/bin/env bash
# Make missing 1 s overview sheets for every downloaded held-out candidate (skips .part files and existing sheets).
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_unseen; SH=~/dance_win/scripts/data/tmp_sheets; mkdir -p $SH
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 8 --w 200 --max_tiles 64
done
