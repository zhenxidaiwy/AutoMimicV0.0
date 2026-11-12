#!/usr/bin/env bash
# push_range.sh: VELOCITY_RANGE of the tracking task's push event
grep -n -A8 "^VELOCITY_RANGE" ~/projects/unitree_rl_mjlab/src/tasks/tracking/tracking_env_cfg.py
