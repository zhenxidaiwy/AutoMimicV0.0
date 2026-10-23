#!/usr/bin/env bash
# Verify the produced held-out test videos: stream info, shot cuts, and a contact sheet per output.
P=~/miniforge3/envs/gmr/bin/python
O=~/projects/dance/live_tests; SH=~/dance_win/scripts/data/tmp_sheets
for f in $O/unseen_*.mp4; do
  printf "%-22s %s\n" "$(basename $f)" "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration -of csv=p=0 $f | tr '\n' ' ')"
  $P -I ~/dance_win/scripts/data/unseen_cuts.py $f
done
for c in sss_1 sss_2 sss_3 gxdsm_1 gxdsm_2 gxdsm_3; do
  $P -I ~/dance_win/scripts/data/sheet.py $O/unseen_$c.mp4 $SH/out_unseen_$c.png --every 0.5 --cols 8 --w 240 --max_tiles 24
done
