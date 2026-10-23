#!/usr/bin/env bash
# restart_after_patch.sh <round> <knob=value> ...: wait for REPORT.md row <round>, stop the harness, patch the knobs in
# state.json, start the harness again with the current code. Bracketed patterns never match this script.
R=$1; shift
until grep -q "^| $R |" ~/dance_win/rl/flip_auto/REPORT.md 2>/dev/null; do sleep 20; done
sleep 5
pkill -f "harnes[s].py --rounds"; sleep 2; pkill -f "train_dance.py.*flipaut[o]_r"; sleep 5
pgrep -af "harnes[s].py|train_danc[e].py" || echo "old harness stopped"
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
python ~/dance_win/rl/flip_auto/set_knob.py "$@"
bash ~/dance_win/rl/flip_auto/run.sh --rounds 16 --iters 1500
