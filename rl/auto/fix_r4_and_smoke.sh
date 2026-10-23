#!/usr/bin/env bash
# Record round 4 as best, compute round 5 knobs, smoke-test the push-grace gate, show the knobs.
cd ~/dance_win/rl/auto && ~/miniforge3/envs/gmr/bin/python -m py_compile harness.py && \
  ~/miniforge3/envs/gmr/bin/python set_best_r4.py
bash ~/dance_win/rl/auto/stop_now.sh 2>&1 | grep -vE "all stopped|removed"
