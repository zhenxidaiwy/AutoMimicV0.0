#!/usr/bin/env bash
# restart_now.sh <knob=value> ...: stop the harness now (the running round restarts), patch knobs, start again.
pkill -f "harnes[s].py --rounds"; sleep 2; pkill -f "train_dance.py.*flipaut[o]_r"; sleep 5
pgrep -af "harnes[s].py|train_danc[e].py" || echo "old harness stopped"
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
python ~/dance_win/rl/flip_auto/set_knob.py "$@"
bash ~/dance_win/rl/flip_auto/run.sh --rounds 16 --iters 1500
