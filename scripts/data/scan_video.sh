#!/usr/bin/env bash
# scan_video.sh <motion dir> <file prefix> <every s> <name>: whole-video contact sheet (one frame every N s, timestamp
# burnt in) to locate the real reps of a move in a long tutorial -> videos/candidates/<name>_scan.jpg
C=~/projects/dance/raw/candidates_2026-10-23/$1
f=$(ls "$C"/$2*.mp4 | head -1)
O=~/dance_win/videos/candidates; mkdir -p $O
dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
n=$(python3 -c "print(int($dur / $3) + 1)")
rows=$(( (n + 11) / 12 ))
ffmpeg -loglevel error -y -i "$f" -vf "fps=1/$3,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=30:fontcolor=yellow:box=1:boxcolor=black@0.7,scale=-2:150,tile=12x$rows" -frames:v 1 "$O/$4_scan.jpg"
echo "$O/$4_scan.jpg ($n frames, $dur s)"
