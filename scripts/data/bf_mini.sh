#!/usr/bin/env bash
# Compact overview sheets (<=30 tiles, 110 px) for given backflip candidates: tmp_sheets_bf/m_av<ID>.png
P=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_backflip; SH=~/dance_win/scripts/data/tmp_sheets_bf
for a in "$@"; do
  $P -I ~/dance_win/scripts/data/sheet.py $RAW/av$a.mp4 $SH/m_av$a.png --every 0.5 --cols 15 --w 110 --max_tiles 30 >/dev/null
done
echo done
