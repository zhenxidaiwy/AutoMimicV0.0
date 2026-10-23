#!/usr/bin/env bash
# A/B of the playback controller on a clip: timeline + analysis for "snap" (old) and "commit" (new).
# Usage: bash bench_ab.sh [clip=gym_sss] [seconds=18]
C=${1:-gym_sss}; S=${2:-18}; O=~/projects/dance_logs/follow_analysis; mkdir -p $O
for PB in snap commit; do
  bash ~/dance_win/live/server.sh --bench $C --bench_seconds $S --playback $PB --rec $O/${C}_$PB.npz 2>&1 | \
    grep -E "playback=|done:|Error|Traceback|line [0-9]+," | cut -c1-160
  echo "== $C playback=$PB"
  cd ~/dance_win/live && ~/miniforge3/envs/gmr/bin/python analyze_follow.py $O/${C}_$PB.npz $C | grep -vE "npz keys"
done
