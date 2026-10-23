#!/usr/bin/env bash
# Re-fetch two truncated ("partial file") negative sources, then fine sheets for the chosen windows.
RAW=~/projects/dance/data/raw_neg
rm -f $RAW/av47296669.mp4 $RAW/av968635540.mp4 ~/dance_win/scripts/data/tmp_sheets_neg/av47296669.png ~/dance_win/scripts/data/tmp_sheets_neg/av968635540.png
bash ~/dance_win/scripts/data/neg_download.sh 47296669 968635540
P=~/miniforge3/envs/gmr/bin/python
for a in 47296669 968635540; do
  ffprobe -v error -show_entries format=duration -of csv=p=0 $RAW/av$a.mp4
  $P -I ~/dance_win/scripts/data/unseen_cuts.py $RAW/av$a.mp4
done
bash ~/dance_win/scripts/data/neg_fine.sh "114567749312109 90 110 0.5 160 10" "117420933122710 86 108 0.5 200 8" \
  "47296669 0 47 1 200 8" "968635540 26 46 0.5 200 8" "117455695450375 143 166 0.5 200 8"
