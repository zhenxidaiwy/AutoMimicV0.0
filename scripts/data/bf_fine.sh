#!/usr/bin/env bash
# Fine sheets for backflip candidates. Usage: bash bf_fine.sh "<aid> <start> <end> [step] [crop|-] [w] [cols]" ...
P=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_backflip; SH=~/dance_win/scripts/data/tmp_sheets_bf
for spec in "$@"; do
  set -- $spec
  C=""; [ -n "$5" ] && [ "$5" != "-" ] && C="--crop $5"
  $P -I ~/dance_win/scripts/data/bf_fine.py $RAW/av$1.mp4 $SH/f_av$1_$2_$3.png --start $2 --end $3 \
    --step ${4:-2} $C --w ${6:-160} --cols ${7:-10}
done
