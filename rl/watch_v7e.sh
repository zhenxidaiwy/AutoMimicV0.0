#!/usr/bin/env bash
# Mid-run check of v7e: curve, rise speed / time-to-stand (eval), stance from falls and from a standing start.
export GETUP_TASK=Dance-Recovery-G1-v7e
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/watch.py getup_v7e_n2048 --every 500
D=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*_getup_v7e_n2048 | tail -1)
CK=$(ls $D/model_*.pt | sort -V | tail -1); echo "ckpt $CK"
CKPT=$CK RUN_FILTER=_getup_v7e_n2048 bash ~/dance_win/rl/eval_getup.sh | grep -E "max pelvis|overall|supine|face-down|side"
bash ~/dance_win/rl/stance_check.sh $CK
bash ~/dance_win/rl/stand_start_check.sh $CK | grep drift
bash ~/dance_win/rl/smooth_check.sh $CK --skip 0.1
it=$(basename $CK .pt | sed 's/model_//')
bash ~/dance_win/rl/demo_getup.sh $CK getup_v7e_iter$it "G1 get-up v7e iter $it (smooth 2-3.5 s get-up)" | grep -E "stood up|video:"
grep -E "Episode_Reward/(rise_schedule|rise_speed|stand_template|waist_limit|stand_up|joint_speed_cap)" \
  ~/projects/dance_logs/train_getup_v7e_n2048.log | tail -5
