#!/usr/bin/env bash
# eval_files.sh <task> <round>: files of that round's eval dir + keys of each npz
export AUTOMIMIC_TASK=$1
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
run=$(python3 -c "import taskcfg; print(taskcfg.run_name($2))")
d=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_${run}/eval | head -1)
ls -la "$d" | cut -c 30-
for f in "$d"/*.npz; do python3 -c "
import sys, numpy as np
z = np.load(sys.argv[1], allow_pickle=True)
print(sys.argv[1].split('/')[-1], {k: z[k].shape for k in z.keys()})" "$f"; done
