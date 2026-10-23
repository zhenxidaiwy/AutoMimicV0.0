#!/usr/bin/env bash
# Routine playback (recognise start -> full replay -> watch again) on gym_sss: events + amplitude vs earlier modes.
O=~/projects/dance_logs/follow_analysis; mkdir -p $O
bash ~/dance_win/live/server.sh --bench gym_sss --bench_seconds 18 --playback routine --rec $O/gym_sss_routine.npz 2>&1 | \
  grep -E "event|done:|Error|Traceback|line [0-9]+," | cut -c1-160
~/miniforge3/envs/gmr/bin/python ~/dance_win/live/spread_stats.py oracle_spec gym_sss_spec gym_sss_routine
