#!/usr/bin/env bash
# Resume from round 5 (model_23499, true round-5 config) with E1 = no random initial episode clocks,
# E2 = E1 + learning rate 3e-4. 60 iterations each.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery; T=~/projects/dance_logs/auto_ab
WARM=$(basename $(ls -d $R/*_auto_r05))
run() {  # name extra-args...
  rm -rf $R/*_abtest$1
  GETUP_NO_RANDOM_EP_LEN=1 GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$T/knobs_A.json bash ~/dance_win/rl/auto/run_mjlab.sh \
    python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations 60 --agent.run-name abtest$1 \
    --agent.logger tensorboard --agent.resume True --agent.load-run $WARM --agent.load-checkpoint model_23499.pt ${@:2} > $T/$1.log 2>&1
  echo "$1 exit=$?"; grep -E "Traceback|Error" $T/$1.log | head -3
  awk -v X=$1 '/Learning iteration/{n++} /Episode_Reward\/stand_up:/{su=$2} /Episode_Reward\/floor_stall:/{fs=$2} /Mean value loss/{vl=$NF} /Time elapsed/{ if (n % 10 == 0) printf "%s iter+%d stand_up %s floor_stall %s value_loss %s\n", X, n, su, fs, vl }' $T/$1.log
  rm -rf $R/*_abtest$1
}
run E1
run E2 --agent.algorithm.learning-rate 0.0003
