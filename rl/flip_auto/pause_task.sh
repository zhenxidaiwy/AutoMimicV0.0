#!/usr/bin/env bash
# pause_task.sh: stop the running harness + training of this session (round stays unrecorded in state.json, so
# `launch_task.sh <task> K` reruns round K from its decision's init checkpoint), list the checkpoints written so far
pkill -f "harnes[s].py --mode llm"
sleep 2
pkill -f "train_danc[e].py"
sleep 3
pgrep -af "harnes[s].py|train_danc[e].py" || echo "stopped"
ls -t ~/projects/dance/runs/logs/rsl_rl/g1_tracking/ | head -2
d=$(ls -td ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*/ | head -1)
ls "$d" | grep model_ | sort -V | tail -3
