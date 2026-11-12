#!/usr/bin/env bash
# list_candidates.sh <motion dir>...: downloaded candidate videos with duration and resolution
cd ~/projects/dance/raw/candidates_2026-10-23 || exit 1
for d in "$@"; do
  echo "== $d"
  for f in "$d"/*.mp4; do
    [ -f "$f" ] || continue
    dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$f")
    res=$(ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 "$f")
    printf '%-75s %6.0fs  %s\n' "$(basename "$f" | cut -c1-75)" "$dur" "$res"
  done
done
