#!/usr/bin/env bash
# preview_clip.sh <motion dir> <file prefix> <start s> <dur s> <name>: cut a preview of a downloaded candidate into
# videos/candidates/ (local only, gitignored) and a 1 frame / 0.5 s contact sheet with timestamps
C=~/projects/dance/raw/candidates_2026-10-23/$1
f=$(ls "$C"/$2*.mp4 | head -1)
O=~/dance_win/videos/candidates; mkdir -p $O
ffmpeg -loglevel error -y -ss $3 -i "$f" -t $4 -an -c:v libx264 -crf 23 -vf scale=-2:540 "$O/$5.mp4"
ffmpeg -loglevel error -y -i "$O/$5.mp4" -vf "fps=2,drawtext=text='%{pts\:hms}':x=6:y=6:fontsize=26:fontcolor=yellow:box=1:boxcolor=black@0.6,scale=-2:180,tile=8x$(( ($4 * 2 + 7) / 8 ))" -frames:v 1 "$O/$5_sheet.jpg"
echo "$O/$5.mp4 (from $3 s of $(basename "$f"))"
