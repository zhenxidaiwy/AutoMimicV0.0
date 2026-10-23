#!/usr/bin/env bash
# Mid-run check of v7b: curve, latest-checkpoint stance (from falls and from a standing start), key reward terms.
export GETUP_TASK=Dance-Recovery-G1-v7b
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/watch.py getup_v7b_n2048 --every 500
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7b_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK | grep drift
grep -E "Episode_Reward/(stand_template|waist_limit|waist_bend|stand_up|standing_posture)" \
  ~/projects/dance_logs/train_getup_v7b_n2048.log | tail -5
