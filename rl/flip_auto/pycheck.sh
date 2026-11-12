#!/usr/bin/env bash
# pycheck.sh file.py ...: syntax check (paths relative to rl/flip_auto) in the training env
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
for f in "$@"; do python -m py_compile "$f" && echo "ok $f"; done
