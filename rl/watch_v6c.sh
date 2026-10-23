#!/usr/bin/env bash
# Mid-run check of v6c: curve, latest-checkpoint stance (torso tilt / waist / stance width), key reward terms.
export GETUP_TASK=Dance-Recovery-G1-v6c
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/watch.py getup_v6c_n2048 --every 500
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v6c_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
bash ~/dance_win/rl/stance_check.sh $CK
grep -E "Episode_Reward/(upright|stand_up|waist_bend|stance|standing_posture|feet_planted)" \
  ~/projects/dance_logs/train_getup_v6c_n2048.log | tail -6
