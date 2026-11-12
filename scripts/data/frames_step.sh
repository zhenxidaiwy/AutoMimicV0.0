#!/usr/bin/env bash
# frames_step.sh <video> <start s> <dur s> <step s> <out.jpg> [height]: fine contact sheet with the ORIGINAL time
# burnt in (pts + start) for frame-accurate cutting
v=$1; ss=$2; t=$3; st=$4; o=$5; h=${6:-320}
n=$(python3 -c "print(int($t / $st) + 1)")
rows=$(( (n + 9) / 10 ))
ffmpeg -loglevel error -y -ss "$ss" -t "$t" -i "$v" -vf "fps=1/$st,drawtext=text='%{pts\:hms\:$ss}':x=4:y=4:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.7,scale=-2:$h,tile=10x$rows" -frames:v 1 "$o"
echo "$o ($n frames)"
