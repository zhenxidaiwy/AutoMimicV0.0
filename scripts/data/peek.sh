#!/usr/bin/env bash
# peek.sh <video> <out.jpg> <frame> [frame ...]: tile the given frames side by side (height 360)
v=$1; o=$2; shift 2
sel=$(printf "eq(n\\,%s)+" "$@"); sel=${sel%+}
ffmpeg -loglevel error -y -i "$v" -vf "select='$sel',scale=-2:360,tile=$#x1" -frames:v 1 "$o"
