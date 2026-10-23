#!/usr/bin/env bash
# Usage: bash squat_template.sh [--save K]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/rl && python make_squat_template.py "$@"
