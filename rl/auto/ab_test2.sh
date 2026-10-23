#!/usr/bin/env bash
# A/B: resume from round 5 for 60 iterations with (A) the TRUE round-5 config (stall 0.4, no still bonus, no squat
# time limit) and (B) the current config; keep checkpoints, then probe each final policy (deterministic) in the
# training config.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
T=~/projects/dance_logs/auto_ab; mkdir -p $T
WARM=$(basename $(ls -d $R/*_auto_r05))
~/miniforge3/envs/gmr/bin/python - <<EOF
import json
k = json.load(open("$A/r05/knobs.json"))
a = dict(k, stall_height=0.4, w_still_bonus=0.0, squat_time_limit=False, w_torso_still=0.0, w_arm_still=0.0,
         stillness_time_only=False)
b = dict(k, stall_height=0.62, w_still_bonus=6.0, squat_time_limit=True, w_torso_still=0.0, w_arm_still=0.0,
         stillness_time_only=False)
json.dump(a, open("$T/knobs_A.json", "w")); json.dump(b, open("$T/knobs_B.json", "w"))
EOF
for X in A B; do
  rm -rf $R/*_abtest$X
  GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$T/knobs_$X.json bash ~/dance_win/rl/auto/run_mjlab.sh \
    python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations 60 --agent.run-name abtest$X \
    --agent.logger tensorboard --agent.resume True --agent.load-run $WARM --agent.load-checkpoint model_23499.pt > $T/$X.log 2>&1
  echo "$X exit=$?"
  awk -v X=$X '/Learning iteration/{n++} /Episode_Reward\/stand_up:/{su=$2} /Episode_Reward\/floor_stall:/{fs=$2} /Mean action noise std|Mean action std/{sd=$NF} /Time elapsed/{ if (n % 10 == 0) printf "%s iter+%d stand_up %s floor_stall %s std %s\n", X, n, su, fs, sd }' $T/$X.log
  CK=$(ls $(ls -d $R/*_abtest$X)/model_*.pt | sort -V | tail -1)
  echo "$X probe of $CK"
  GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$T/knobs_$X.json bash ~/dance_win/rl/auto/run_mjlab.sh \
    python ~/dance_win/rl/auto/train_env_probe.py --ckpt $CK --n 256 2>&1 | grep -E "^t=(2|4|8)"
done
