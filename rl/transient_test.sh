#!/usr/bin/env bash
# Reset transient per fallen pose with the corrected (true) supine pose, two drop heights (v7c final policy).
CK=~/projects/dance/runs/logs/rsl_rl/g1_recovery/2026-10-20_19-06-56_getup_v7c_n2048/model_15499.pt
echo "== true supine, no extra height"
bash ~/dance_win/rl/smooth_check.sh $CK --n 128 --seconds 1 --true_supine | grep transient
echo "== true supine, +0.05 m all poses"
bash ~/dance_win/rl/smooth_check.sh $CK --n 128 --seconds 1 --true_supine --pose_extra 0.05 0.05 0.05 0.05 | grep transient
