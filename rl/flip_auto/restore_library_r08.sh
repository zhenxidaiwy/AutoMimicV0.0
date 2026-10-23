#!/usr/bin/env bash
# restore_library_r08.sh: library back to the end of round 8 (frozen snapshot) + the r08 critic history, i.e. undo the
# prematurely applied r09 decision
cd ~/dance_win/rl/flip_auto || exit 1
cp library.json /tmp/library_before_restore.json
cp runs/rules_v1_r01-r08/library.json library.json && chmod u+w library.json
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
EV=~/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-23_01-39-50_flipauto_r08/eval
python critic.py $EV/flip_auto_model_5500_record.npz ~/projects/dance/dataset/backflip_3/labels_50fps.npz \
  $EV/flip_auto_model_5500.mp4 --round 8 > /dev/null
python3 lib_summary.py | head -n 14
