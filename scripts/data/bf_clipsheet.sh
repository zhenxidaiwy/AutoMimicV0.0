#!/usr/bin/env bash
# Frame-indexed sheets of cut backflip clips (label f<N> = clip frame at 30 fps). Usage: bash bf_clipsheet.sh "<k> [step] [crop|-] [w] [cols]" ...
P=~/miniforge3/envs/gmr/bin/python
C=~/projects/dance/data/clips; SH=~/dance_win/scripts/data/tmp_sheets_bf
for spec in "$@"; do
  set -- $spec
  X=""; [ -n "$3" ] && [ "$3" != "-" ] && X="--crop $3"
  $P -I ~/dance_win/scripts/data/bf_fine.py $C/backflip_$1.mp4 $SH/clip_backflip_$1.png --start 0 --end 99 \
    --step ${2:-2} $X --w ${4:-90} --cols ${5:-25}
done
