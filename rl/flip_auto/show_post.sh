#!/usr/bin/env bash
# show_post.sh <run dir> <eval tag> <out name> <first post frame>: copy an eval video into videos/backflip/auto and
# make a sheet of the post-reference part (every 25th frame = 0.5 s)
src=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1/eval/flip_$2.mp4
out=~/dance_win/videos/backflip/auto/$3
mkdir -p "$(dirname $out)"
cp "$src" "$out.mp4"
ffmpeg -loglevel error -y -i "$out.mp4" -vf "select='gte(n\,$4)*not(mod(n-$4\,25))',drawtext=text='%{n}':x=8:y=8:fontsize=40:fontcolor=yellow:box=1:boxcolor=black@0.6,scale=-2:240,tile=6x2" -frames:v 1 "${out}_post_sheet.jpg"
ls -la "$out.mp4" "${out}_post_sheet.jpg"
