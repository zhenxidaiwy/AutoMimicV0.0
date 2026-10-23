#!/usr/bin/env bash
# Check the new sway metrics on round 4 and that the auto config (torso/arm still terms) trains.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
CK=$(ls -d $R/*_auto_r04)/model_22000.pt; T=~/projects/dance_logs/auto_selftest; mkdir -p $T
export GETUP_TASK=Dance-Recovery-G1-auto
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $T/f.json > $T/s1.log 2>&1
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $T/s.json --stand_start > $T/s2.log 2>&1
grep -hE "sway|angv|success\"|Traceback|Error" $T/f.json $T/s.json $T/s1.log $T/s2.log | head -12
bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/train_getup.py -- --env.scene.num-envs 256 \
  --agent.max-iterations 3 --agent.run-name autosmoke --agent.logger tensorboard --agent.resume True \
  --agent.load-run $(basename $(ls -d $R/*_auto_r04)) --agent.load-checkpoint model_22000.pt > $T/smoke.log 2>&1
echo "smoke exit=$?"; rm -rf $R/*_autosmoke
grep -E "Traceback|Error|line [0-9]+," $T/smoke.log | tail -4
grep -E "Episode_Reward/(torso_still|arm_still|feet_move_stand)" $T/smoke.log | tail -3
~/miniforge3/envs/gmr/bin/python -m py_compile ~/dance_win/rl/auto/harness.py && echo "harness ok"
