#!/usr/bin/env bash
# grab candidate frames for the main figure into paper/fig_assets/raw/ (frame index n, original resolution)
O=~/dance_win/paper/fig_assets/raw; mkdir -p $O
grab() { ffmpeg -loglevel error -y -i "$1" -vf "select='eq(n\,$2)'" -frames:v 1 "$O/$3.jpg"; }
C=~/projects/dance/data/clips/backflip_3.mp4
Q=~/dance_win/data/qa/backflip_3
E=~/dance_win/policies/backflip_r04_best/eval.mp4
for n in 40 55 62 66 70; do grab $C $n human_$n; done
for n in 55 62 66; do grab $Q/gvhmr.mp4 $n smpl_$n; done
for n in 55 62 66; do grab $Q/qa.mp4 $n qa_$n; done
for n in 82 95 101 108 115 126 140; do grab $E $n eval_$n; done
ffprobe -v error -select_streams v -show_entries stream=width,height -of csv=p=0 $C $Q/gvhmr.mp4 $Q/qa.mp4 $E
ls $O | wc -l
