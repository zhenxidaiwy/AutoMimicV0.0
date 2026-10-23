#!/usr/bin/env bash
# analyze.sh [round]: analysis pack for the LLM decider (see analyze_round.py)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
python analyze_round.py "$@"
