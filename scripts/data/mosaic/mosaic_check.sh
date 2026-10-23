#!/usr/bin/env bash
# 8 evenly spaced frames from each mosaicked dance clip -> one sheet for a manual privacy check
cd '<repo>/data/source_clips_mosaic' || exit 1
O=/mnt/c/Users/user/AppData/Local/Temp/claude/d---------NUS-----------videoLA/e879becf-b1ba-4a34-858a-b36f96cc984f/scratchpad
for c in bda_zhao_sss bda2_gxdsm_full; do
  n=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $c.mp4)
  s=$(( n / 8 ))
  ffmpeg -loglevel error -y -i $c.mp4 -vf "select='not(mod(n\,$s))',scale=-2:300,tile=8x1" -frames:v 1 $O/mosaic_$c.png
done
echo ok
