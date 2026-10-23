#!/usr/bin/env bash
# Wait for round 0 to be fully recorded, restart the harness with the edited rules, and keep it running.
A=~/projects/dance_logs/auto
until [ -f $A/state.json ] && [ -f $A/r00/metrics.json ]; do sleep 20; done
sleep 30  # let the harness launch round 1 so the kill below catches it in a known state
bash ~/dance_win/rl/auto/restart_with_new_rules.sh
cd ~/dance_win/rl/auto && exec ~/miniforge3/envs/gmr/bin/python -u harness.py --warm unused --rounds 10 --iters 1500
