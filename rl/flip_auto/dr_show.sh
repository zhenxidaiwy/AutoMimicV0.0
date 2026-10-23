#!/usr/bin/env bash
# dr_show.sh: print the tracking task's event (domain randomisation) config and the G1 overrides
P=/home/user/miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab/tasks/tracking
sed -n '160,205p' $P/tracking_env_cfg.py
echo ----
sed -n '50,100p' $P/config/g1/env_cfgs.py
