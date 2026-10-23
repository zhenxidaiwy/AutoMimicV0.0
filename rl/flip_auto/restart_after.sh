#!/usr/bin/env bash
# restart_after.sh <round>: wait until REPORT.md has the row of <round>, then stop the harness (and the trainer of the
# next round it already started) and start it again with the current code. Bracketed patterns never match this script.
R=$1
until grep -q "^| $R |" ~/dance_win/rl/flip_auto/REPORT.md 2>/dev/null; do sleep 20; done
sleep 5
pkill -f "harnes[s].py --rounds"; sleep 2; pkill -f "train_dance.py.*flipaut[o]_r"; sleep 5
pgrep -af "harnes[s].py|train_danc[e].py" || echo "old harness stopped"
bash ~/dance_win/rl/flip_auto/run.sh --rounds 14 --iters 1500
