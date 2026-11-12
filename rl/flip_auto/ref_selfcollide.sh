#!/usr/bin/env bash
# ref_selfcollide.sh <task>: ref_selfcollide.py on the task's training reference
export AUTOMIMIC_TASK=$1
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
eval "$(python3 -c "
import taskcfg as t
print(f'DS={t.DS}; VAR={t.VAR}')")"
python ref_selfcollide.py $DS/g1_${VAR}_50fps.npz
python ref_feet_z.py $DS/g1_${VAR}_50fps.npz ${2:-10}
