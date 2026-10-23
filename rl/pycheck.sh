#!/usr/bin/env bash
# Syntax check of the get-up package + scripts (no GPU, no import side effects).
~/miniforge3/envs/gmr/bin/python -m py_compile ~/dance_win/rl/getup/__init__.py ~/dance_win/rl/getup/mdp.py \
  ~/dance_win/rl/getup/env_cfg.py ~/dance_win/rl/stance_check.py && echo "py_compile ok"
