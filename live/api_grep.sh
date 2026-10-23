#!/usr/bin/env bash
P=~/miniforge3/envs/unitree_rl_mjlab/lib/python3.11/site-packages/mjlab
grep -n "def root_link_ang_vel_w\|def root_link_lin_vel_w\|def root_link_vel_w" $P/entity/data.py | head
grep -rn "def forward\b\|def forward(" $P/sim/*.py | head
grep -n "self._action\b\|self._prev_action\|self._action =\|def action\b\|def prev_action" $P/managers/action_manager.py | head
grep -n "def anchor_quat_w\|def robot_anchor_quat_w\|anchor_body_name\|def anchor_pos_w" $P/tasks/tracking/mdp/commands.py | head
grep -n "def get_observations" -A6 $P/rl/vecenv_wrapper.py | head -12
