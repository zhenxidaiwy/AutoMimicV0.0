#!/usr/bin/env bash
# grab_frames.sh <video> <out.jpg> <t1> <t2> ...: full-resolution frames at the given times, side by side, with a
# 100 px y-grid (to read crop rows)
v=$1; o=$2; shift 2
i=0; in=""; fl=""
for t in "$@"; do
  ffmpeg -loglevel error -y -ss "$t" -i "$v" -frames:v 1 -vf "drawgrid=w=iw:h=100:t=1:c=red@0.6,drawtext=text='t=$t':x=8:y=8:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.7" /tmp/gf_$i.png
  in="$in -i /tmp/gf_$i.png"; fl="$fl[$i:v]"; i=$((i+1))
done
ffmpeg -loglevel error -y $in -filter_complex "${fl}hstack=inputs=$i" "$o" && echo "$o"
