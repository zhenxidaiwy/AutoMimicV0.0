#!/usr/bin/env bash
# Offline check of fall -> learned get-up -> resume dancing: replay a held-out clip's keypoints for 25 s with test
# pushes at 4 s and 15 s.  Usage: bash bench_getup.sh [clip=gym_sss]
bash ~/dance_win/live/server.sh --bench ${1:-gym_sss} --bench_seconds 25 --push_at 4,15 2>&1 | \
  grep -E "\[bench\]|\[server\]|Error|Traceback|line [0-9]+,|assert"
