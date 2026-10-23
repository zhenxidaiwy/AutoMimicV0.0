#!/usr/bin/env bash
# Current time, GPU usage, running pipeline processes, tail of a clip log.
# Usage: bash job_status.sh [clip_id]
date +%T
nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader
ps -eo pid,etime,args | grep -E "demo.py|retarget_headless|csv_to_npz|yt_dlp" | grep -v grep | cut -c1-120
[ -n "$1" ] && tail -c 600 ~/projects/dance_logs/clip_$1.log | tr '\r' '\n' | tail -4
