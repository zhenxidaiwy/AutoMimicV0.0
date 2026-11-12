#!/usr/bin/env bash
# qa_vs_gvhmr.sh <clip>: one video, top = GVHMR render (in-camera | global), bottom = retarget QA (source | G1), same
# height and frame count -> data/qa/<clip>/qa_vs_gvhmr.mp4
Q=~/dance_win/data/qa/$1
ffmpeg -loglevel error -y -i $Q/gvhmr.mp4 -i $Q/qa.mp4 -filter_complex \
  "[0:v]scale=-2:480,pad=1100:480:0:0,drawtext=text='GVHMR (human)':x=8:y=8:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6[a];[1:v]scale=-2:480,pad=1100:480:0:0,drawtext=text='retarget (G1)':x=8:y=8:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6[b];[a][b]vstack" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p $Q/qa_vs_gvhmr.mp4 && echo $Q/qa_vs_gvhmr.mp4
