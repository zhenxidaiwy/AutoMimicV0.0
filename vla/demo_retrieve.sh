#!/usr/bin/env bash
# Compose a demo video from a retrieve_loop run and make a contact sheet. Usage: bash demo_retrieve.sh <name> "<title>"
P=~/miniforge3/envs/gmr/bin/python
out=$($P ~/dance_win/vla/demo_video.py $1 --dir retrieve_loop --title "$2" | tail -1)
$P ~/dance_win/scripts/data/sheet.py $out ${out%.mp4}_sheet.png --every 0.5 --cols 4 --w 480 --max_tiles 16
