#!/usr/bin/env bash
# Resume tests with the TRUE round-5 config (knobs_A): C = round 5 intermediate checkpoint model_23000,
# D = round 4 model_22000 (round 5's own starting point, which trained fine at 13:42).
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery; T=~/projects/dance_logs/auto_ab
rm -rf $R/*_abtestA $R/*_abtestB
run() {  # name run_dir_glob ckpt
  rm -rf $R/*_abtest$1
  GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$T/knobs_A.json bash ~/dance_win/rl/auto/run_mjlab.sh \
    python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations 40 --agent.run-name abtest$1 \
    --agent.logger tensorboard --agent.resume True --agent.load-run $(basename $(ls -d $R/*_$2)) \
    --agent.load-checkpoint $3 > $T/$1.log 2>&1
  echo "$1 exit=$?"
  awk -v X=$1 '/Learning iteration/{n++} /Episode_Reward\/stand_up:/{su=$2} /Episode_Reward\/floor_stall:/{fs=$2} /Time elapsed/{ if (n % 10 == 0) printf "%s iter+%d stand_up %s floor_stall %s\n", X, n, su, fs }' $T/$1.log
  rm -rf $R/*_abtest$1
}
run C auto_r05 model_23000.pt
run D auto_r04 model_22000.pt
