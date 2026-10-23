#!/usr/bin/env bash
# Trial cuts for negative batch 2: normalise a window exactly like make_neg2_tests.sh into tmp_trial_neg2/,
# then a contact sheet + cut detection, so the 4:3 crop / feet / cuts can be checked before committing.
# Usage: bash neg2_trial.sh "<aid> <start> <end> [every] [w] [cols]" ...
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_neg2; T=~/dance_win/scripts/data/tmp_trial_neg2; mkdir -p $T
VF="crop=w='min(iw,ih*4/3)':h=ih,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
for spec in "$@"; do
  set -- $spec
  o=$T/av$1_$2_$3
  ffmpeg -loglevel error -y -i $RAW/av$1.mp4 -ss $2 -to $3 -an -vf "$VF" -c:v libx264 -crf 23 -pix_fmt yuv420p $o.mp4
  $PY -I ~/dance_win/scripts/data/unseen_cuts.py $o.mp4
  $PY -I ~/dance_win/scripts/data/sheet.py $o.mp4 $o.png --every ${4:-1} --w ${5:-120} --cols ${6:-10} --max_tiles 40 >/dev/null
done
