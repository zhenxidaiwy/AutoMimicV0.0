#!/usr/bin/env bash
# Inspect the user's video and make a contact sheet (for my own check of what it shows).
V=~/dance_win/videos/follow/web_selftest/51af839c2f28af6799b9ef2e4a3a6589.mp4
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,nb_frames:format=duration -of default=nw=1 $V
~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/sheet.py $V ~/dance_win/videos/follow/user_video_sheet.png --every 1.0 --cols 6 --w 1800 --max_tiles 24 | tail -1
