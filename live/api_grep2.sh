#!/usr/bin/env bash
P=~/miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab
grep -n "def write_external_wrench\|def set_external\|external_force\|xfrc_applied" $P/entity/entity.py $P/entity/data.py | head
grep -n "def apply_external_force_torque" -A25 $P/envs/mdp/events.py | head -40
grep -n "def body_com_pos_w\|def body_link_pos_w\|def body_com_quat_w" $P/entity/data.py | head
