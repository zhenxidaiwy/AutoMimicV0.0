#!/usr/bin/env bash
# peek_rows.sh <video> <out.jpg> <width> <frame> [frame ...]: stack the given frames vertically, scaled to <width>
v=$1; o=$2; w=$3; shift 3
sel=$(printf "eq(n\\,%s)+" "$@"); sel=${sel%+}
ffmpeg -loglevel error -y -i "$v" -vf "select='$sel',scale=$w:-2,tile=1x$#" -frames:v 1 "$o"
