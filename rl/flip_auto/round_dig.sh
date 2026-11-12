#!/usr/bin/env bash
# round_dig.sh <task> <round> <ckpt> <first> <last> <step> joint ...: robot vs reference joints of that checkpoint's
# eval record (step-2 analysis helper; ckpt e.g. model_1000)
export AUTOMIMIC_TASK=$1; R=$2; C=$3; shift 3
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
run=$(python3 -c "import taskcfg; print(taskcfg.run_name($R))")
rec=$(ls ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_${run}/eval/flip_auto_${C}_record.npz | head -1)
echo "record: $rec"
python3 joint_table.py "$rec" "$@"
