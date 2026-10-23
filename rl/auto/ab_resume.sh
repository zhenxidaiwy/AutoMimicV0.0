#!/usr/bin/env bash
# Controlled experiment: resume from round 5 for 150 iterations with (A) round 5's exact knobs.
# Does the get-up collapse happen even without any reward change?
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
pgrep -fa "harness|train_getup" || echo "harness stopped"
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
for d in $R/*_auto_r$(printf "%02d" $N); do [ -d "$d" ] && rm -rf "$d" && echo "removed half-finished $d"; done
rm -rf $A/r$(printf "%02d" $N)
WARM=$(basename $(ls -d $R/*_auto_r05))
T=~/projects/dance_logs/auto_ab; mkdir -p $T
GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$A/r05/knobs.json bash ~/dance_win/rl/auto/run_mjlab.sh \
  python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 2048 --agent.max-iterations 150 --agent.run-name abtestA \
  --agent.logger tensorboard --agent.resume True --agent.load-run $WARM --agent.load-checkpoint model_23499.pt > $T/A.log 2>&1
echo "A exit=$?"
awk '/Learning iteration/{n++} /Episode_Reward\/stand_up:/{su=$2} /Episode_Reward\/floor_stall:/{fs=$2} /Mean action noise std|Mean action std/{sd=$NF} /Time elapsed/{ if (n % 15 == 0) printf "A iter+%d stand_up %s floor_stall %s std %s\n", n, su, fs, sd }' $T/A.log
rm -rf $R/*_abtestA
