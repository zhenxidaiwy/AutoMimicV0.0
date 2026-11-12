#!/usr/bin/env bash
# push_cfg.sh <task> <round>: the push / randomisation events of the tracking task + the hold rewards in that round's log
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
grep -n -A6 "push\|EventTermCfg" ~/projects/unitree_rl_mjlab/src/tasks/tracking/tracking_env_cfg.py | grep -v "^--$" | head -60
export AUTOMIMIC_TASK=$1
cd ~/dance_win/rl/flip_auto || exit 1
f=$(python3 -c "import taskcfg; print(taskcfg.train_log($2))")
grep -E "hold_spot|base_still|stand_quiet|Mean episode length" "$f" | tail -4
