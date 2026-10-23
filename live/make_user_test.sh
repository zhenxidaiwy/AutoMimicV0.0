#!/usr/bin/env bash
# The user's own test video -> live_tests/user_1.mp4 (neutral name: no hint about the dance).
# Phone screen recording 576x1280: crop away most of the app UI (rows 160-1180), then the standard normalisation.
V=~/dance_win/videos/follow/web_selftest/51af839c2f28af6799b9ef2e4a3a6589.mp4
O=~/projects/dance/live_tests/user_1.mp4
ffmpeg -loglevel error -y -i $V -vf "crop=576:1020:0:160,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1" \
  -an -c:v libx264 -crf 18 -pix_fmt yuv420p $O
ffprobe -v error -show_entries stream=width,height,nb_frames -of default=nw=1 $O
