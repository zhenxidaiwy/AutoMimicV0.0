#!/usr/bin/env bash
# sheet_grid.sh <video> <out.jpg> <first> <last> <step> <cols>: contact sheet labelled with the ORIGINAL frame index
v=$1; o=$2; a=$3; b=$4; s=$5; c=$6
n=$(( (b - a) / s + 1 )); r=$(( (n + c - 1) / c ))
ffmpeg -loglevel error -y -i "$v" -vf "drawtext=text='%{n}':x=5:y=5:fontsize=40:fontcolor=yellow:box=1:boxcolor=black@0.6,select='between(n\,$a\,$b)*not(mod(n-$a\,$s))',scale=-2:300,tile=${c}x${r}" -frames:v 1 "$o"
