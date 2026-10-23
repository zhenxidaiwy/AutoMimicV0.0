#!/usr/bin/env bash
# Verifier: frame count / fps of the get-up side-by-side video + a few frames into sim2sim/verify_frames/
V=~/dance_win/videos/sim2sim/getup_side_by_side.mp4
OUT=~/dance_win/sim2sim/verify_frames
mkdir -p $OUT
ffprobe -v error -select_streams v:0 -count_frames -show_entries stream=nb_read_frames,r_frame_rate,width,height,duration -of default=nw=1 $V
# frames: 150 per pose (6 s at 25 fps); pick early/mid/late of pose 0 and pose 2, plus last frame
for f in 0 40 120 149 190 340 420 599; do
  ffmpeg -v error -y -i $V -vf "select=eq(n\,$f)" -vsync 0 -frames:v 1 $OUT/getup_f$f.png
done
ls -la $OUT
