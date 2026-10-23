#!/usr/bin/env bash
# Download held-out candidate videos (html5 360p mp4 via the mobile page; desktop/API are 412-blocked)
# into ~/projects/dance/data/raw_unseen and make a 1 s overview contact sheet in ~/dance_win/scripts/data/tmp_sheets.
# Personal research use only. Usage: bash unseen_download.sh <aid|BVid> [...]
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_unseen; SH=~/dance_win/scripts/data/tmp_sheets; mkdir -p $RAW $SH
$PY -I ~/dance_win/scripts/data/unseen_fetch.py get $RAW "$@"
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 8 --w 200 --max_tiles 64
done
