#!/usr/bin/env bash
# Download negative-test candidates (html5 360p via the mobile page) into ~/projects/dance/data/raw_neg
# and make 1 s overview sheets in ~/dance_win/scripts/data/tmp_sheets_neg. Personal research use only.
# Usage: bash neg_download.sh <aid|BVid> [...]
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_neg; SH=~/dance_win/scripts/data/tmp_sheets_neg; mkdir -p $RAW $SH
$PY -I ~/dance_win/scripts/data/unseen_fetch.py get $RAW "$@"
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 8 --w 200 --max_tiles 64
done
