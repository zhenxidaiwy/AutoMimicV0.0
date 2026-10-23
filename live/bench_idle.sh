#!/usr/bin/env bash
# Routine playback with the get-up policy as the standing controller: gym_sss 18 s with pushes while standing /
# dancing, and a long "nobody there" stretch (bench clip loops, then the feeder keeps the clip running).
~/miniforge3/envs/unitree_rl_mjlab/bin/python -m py_compile ~/dance_win/live/server.py && echo "compile ok"
bash ~/dance_win/live/server.sh --bench gym_sss --bench_seconds 24 --push_at 3,10,19 2>&1 | \
  grep -E "event|done:|Error|Traceback|line [0-9]+,|NameError|UnboundLocal" | cut -c1-170
