#!/usr/bin/env bash
# task_status.sh <task> <round>: harness log tail, task_init result, training config lines and progress of a round
export AUTOMIMIC_TASK=$1
cd ~/dance_win/rl/flip_auto || exit 1
f=$(python3 -c "import taskcfg; print(taskcfg.train_log($2))")
tail -n 3 ~/projects/dance_logs/harness_$1.log 2>/dev/null | cut -c 1-250
tail -n 2 ~/projects/dance_logs/task_init_$1.log 2>/dev/null | cut -c 1-300
grep -E "hand collision|action delay|flip terminations|library fixes" "$f" 2>/dev/null | cut -c 1-220
grep "Learning iteration" "$f" 2>/dev/null | tail -1
grep "Mean episode length" "$f" 2>/dev/null | tail -1
pgrep -af "harnes[s].py|train_danc[e].py" | cut -c 1-120
