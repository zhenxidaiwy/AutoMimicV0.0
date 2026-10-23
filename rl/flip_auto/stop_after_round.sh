#!/usr/bin/env bash
# stop_after_round.sh K: wait until round K is evaluated (state.json has K rounds), then stop the harness so the
# next round does not start under the old code. Does not start anything (LLM mode: the agent decides next).
K=$1
cd ~/dance_win/rl/flip_auto || exit 1
while true; do
  n=$(python3 -c "import json; print(len(json.load(open('state.json'))['rounds']))" 2>/dev/null)
  [ "${n:-0}" -ge "$K" ] && break
  sleep 30
done
sleep 5
pkill -f "harnes[s].py --rounds"; sleep 2; pkill -f "train_dance.py.*flipaut[o]_r"; sleep 3
pgrep -af "harnes[s].py|train_danc[e].py" || echo "harness stopped after round $K"
tail -n 30 REPORT.md
