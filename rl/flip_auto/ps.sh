#!/usr/bin/env bash
# ps.sh: harness-related processes + state round count + latest training iteration
pgrep -af "harnes[s].py|train_danc[e].py|stop_after_roun[d]|launch_ll[m]" | cut -c 1-160
cd ~/dance_win/rl/flip_auto && python3 -c "import json; print('state rounds:', len(json.load(open('state.json'))['rounds']))"
f=$(ls -t ~/projects/dance_logs/train_flipauto_r*.log | head -1); echo "$f"; grep 'Learning iteration' "$f" | tail -n 1
ls -la --time-style=+%H:%M state.json | cut -c 30-
