#!/usr/bin/env bash
# Contact sheet of an eval video. Usage: bash eval_sheet.sh <run-substring> <model_XXXX>
d=$(ls -d ~/dance_win/videos/*$1 | tail -1)
~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/sheet.py $d/$2.mp4 $d/$2_sheet.png --every 0.4 --cols 6 --w 320
