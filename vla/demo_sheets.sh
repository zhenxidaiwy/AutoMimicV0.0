#!/usr/bin/env bash
# Contact sheets of the demo videos (for a quick visual check).
P=~/miniforge3/envs/gmr/bin/python
for f in ~/dance_win/videos/vla/*_demo.mp4; do
  $P ~/dance_win/scripts/data/sheet.py $f ${f%.mp4}_sheet.png --every 0.5 --cols 4 --w 480 --max_tiles 16
done
