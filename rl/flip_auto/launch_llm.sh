#!/usr/bin/env bash
# launch_llm.sh K: run exactly round K in LLM mode (needs decisions/rKK.json), then exit so the agent is notified.
K=$1
f=~/dance_win/rl/flip_auto/decisions/r$(printf %02d $K).json
[ -f "$f" ] || { echo "missing $f"; exit 1; }
pgrep -af "harnes[s].py|train_danc[e].py" && { echo "harness/training already running"; exit 1; }
bash ~/dance_win/rl/flip_auto/run.sh --mode llm --rounds $K --iters 1500
echo "round $K finished"; tail -n 40 ~/dance_win/rl/flip_auto/REPORT.md
