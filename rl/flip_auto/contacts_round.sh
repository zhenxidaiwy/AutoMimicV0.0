#!/usr/bin/env bash
# contacts_round.sh <task> <round> <ckpt> [first last]: floor_contacts.py of that round's eval record, robot and reference
export AUTOMIMIC_TASK=$1
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
run=$(python3 -c "import taskcfg; print(taskcfg.run_name($2))")
rec=$(ls ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_${run}/eval/flip_auto_$3_record.npz | head -1)
python floor_contacts.py "$rec" ${4:-0} ${5:--1}
python floor_contacts.py "$rec" ${4:-0} ${5:--1} --ref
