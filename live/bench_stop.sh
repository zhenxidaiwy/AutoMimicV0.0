#!/usr/bin/env bash
# Routine playback with the 0.3 s stop rule: events on a 闪身步 clip (flashes with stand pauses) and a
# 狗熊哆嗦毛 clip (both held-out performers from the dataset).
~/miniforge3/envs/unitree_rl_mjlab/bin/python -m py_compile ~/dance_win/live/server.py && echo "compile ok"
for C in gym_sss bda_ming_gxdsm_a; do
  echo "== $C"
  bash ~/dance_win/live/server.sh --bench $C --bench_seconds 12 2>&1 | \
    grep -E "event|done:|Error|Traceback|line [0-9]+,|NameError|UnboundLocal" | cut -c1-150
done
