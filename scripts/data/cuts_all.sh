#!/usr/bin/env bash
# Run the cut detector on every cut clip in ~/projects/dance/data/clips.
P=~/miniforge3/envs/gmr/bin/python
for f in ~/projects/dance/data/clips/*.mp4; do $P ~/dance_win/scripts/data/detect_cuts.py "$f" "$@"; done
