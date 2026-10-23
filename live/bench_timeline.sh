#!/usr/bin/env bash
# Timeline recording for latency / amplitude analysis: replay a clip's keypoints (3 loops), no pushes.
# Usage: bash bench_timeline.sh [clip=gym_sss] [seconds=18]
mkdir -p ~/projects/dance_logs/follow_analysis
bash ~/dance_win/live/server.sh --bench ${1:-gym_sss} --bench_seconds ${2:-18} \
  --rec ~/projects/dance_logs/follow_analysis/${1:-gym_sss}_timeline.npz 2>&1 | \
  grep -E "\[server\]|Error|Traceback|line [0-9]+,"
