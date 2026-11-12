#!/usr/bin/env bash
# closeup.sh <video> <out_prefix> <first> <last> [cols]: full-resolution frames first..last of a 50 fps eval video,
# tiled cols per row (default 4), 12 frames per image, frame number burnt in - for frame-by-frame detail review
v=$1; o=$2; a=$3; b=$4; c=${5:-4}
mkdir -p "$(dirname "$o")"
for ((s=a; s<=b; s+=12)); do
  e=$((s+11 > b ? b : s+11)); n=$((e-s+1)); r=$(( (n+c-1)/c ))
  ffmpeg -loglevel error -y -i "$v" -vf "select='between(n\,$s\,$e)',drawtext=text='%{eif\:n+$s\:d}':x=10:y=10:fontsize=36:fontcolor=yellow:box=1:boxcolor=black@0.6,tile=${c}x${r}" \
    -frames:v 1 -vsync vfr "${o}_$(printf %03d $s)-$(printf %03d $e).jpg" && echo "${o}_$(printf %03d $s)-$(printf %03d $e).jpg"
done
