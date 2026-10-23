#!/usr/bin/env bash
P=~/miniforge3/envs/gmr/bin/python
for n in switch_test bda_ming_gxdsm_a; do
  $P ~/dance_win/scripts/data/sheet.py ~/dance_win/live/video_test_$n.mp4 ~/dance_win/live/video_test_${n}_sheet.png --every 1 --cols 4 --w 520 --max_tiles 16
done
