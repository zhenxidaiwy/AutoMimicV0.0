#!/usr/bin/env bash
# log_terms.sh <task> <round>: last logged value of every Episode_Reward / Episode_Termination / episode length line
# of that round's training log, plus the episode length every 100 iterations
export AUTOMIMIC_TASK=$1
cd ~/dance_win/rl/flip_auto || exit 1
f=$(python3 -c "import taskcfg; print(taskcfg.train_log($2))")
echo "$f"
awk '/Episode_Reward|Episode_Termination|Mean episode length|Mean reward/ {v[$1]=$0} END {for (k in v) print v[k]}' "$f" | sort
echo "--- episode length by iteration"
awk '/Learning iteration/ {split($3, a, "/"); it=a[1]} /Mean episode length/ {if (it % 100 == 0 && it != last) {printf "%s:%s ", it, $NF; last=it}} END {print ""}' "$f"
