#!/usr/bin/env bash
# wait_round.sh K: block until the harness log says round K is done (or the harness died), then print the summary.
# Used to get a completion notification for a round launched in an earlier agent session.
K=$1
LOG=~/projects/dance_logs/flip_auto.log
while true; do
  grep -q "=== round $K done" $LOG && break
  pgrep -f "harnes[s].py" >/dev/null || { echo "harness not running and round $K not done"; break; }
  sleep 60
done
grep "=== round $K done" $LOG | tail -1 | cut -c 1-400
ls ~/dance_win/rl/flip_auto/analysis/ | grep "r$(printf %02d $K)"
