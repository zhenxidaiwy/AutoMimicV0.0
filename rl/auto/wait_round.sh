#!/usr/bin/env bash
# Block until harness round K has its metrics (or the harness died), then print that round's report section.
# Usage: bash wait_round.sh K
K=$(printf "%02d" $1); A=~/projects/dance_logs/auto
while [ ! -f $A/r$K/metrics.json ]; do
  if ! pgrep -f "harness.py" > /dev/null && ! pgrep -f "auto/start.sh" > /dev/null; then echo "harness not running"; break; fi
  sleep 60
done
tail -n 6 $A/harness.log
awk -v r="## Round $1 " 'index($0, r) == 1 {p = 1} p && /^## Round / && index($0, r) != 1 {p = 0} p' ~/dance_win/rl/auto/REPORT.md
