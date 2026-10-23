#!/usr/bin/env bash
# Stop the harness immediately (mid-round), drop the half-finished round, smoke-test the current auto config from
# the warm-start checkpoint in state.json. Resume afterwards with resume.sh.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; pkill -f "metrics.py"; pkill -f "demo_getup"; sleep 5
pgrep -fa "harness|train_getup|metrics.py|demo_getup" || echo "all stopped"
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
NN=$(printf "%02d" $N)
for d in $R/*_auto_r$NN; do [ -d "$d" ] && rm -rf "$d" && echo "removed half-finished $d"; done
rm -rf $A/r$NN
WARM=$(~/miniforge3/envs/gmr/bin/python -c "import json;s=json.load(open('$A/state.json'));print(s['warm'])")
WCK=$(~/miniforge3/envs/gmr/bin/python -c "import json;s=json.load(open('$A/state.json'));print(s.get('warm_ckpt') or 'model_.*.pt')")
echo "smoke test from $WARM/$WCK"
GETUP_TASK=Dance-Recovery-G1-auto bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/train_getup.py -- \
  --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name autosmoke --agent.logger tensorboard \
  --agent.resume True --agent.load-run $WARM --agent.load-checkpoint $WCK > ~/projects/dance_logs/auto_smoke.log 2>&1
echo "exit=$?"; rm -rf $R/*_autosmoke
grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/auto_smoke.log | tail -6
grep -E "Episode_Reward/(feet_move_stand|feet_spread|floor_stall|stand_up)" ~/projects/dance_logs/auto_smoke.log | tail -4
