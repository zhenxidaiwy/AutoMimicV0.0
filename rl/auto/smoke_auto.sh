#!/usr/bin/env bash
# 3-iteration smoke test of the current auto task (default knobs) from the latest finished harness run.
R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
WARM=$(basename $(ls -d $R/*_auto_r00 | tail -1))
GETUP_TASK=Dance-Recovery-G1-auto bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/train_getup.py -- \
  --env.scene.num-envs 256 --agent.max-iterations 3 --agent.run-name autosmoke --agent.logger tensorboard \
  --agent.resume True --agent.load-run $WARM > ~/projects/dance_logs/auto_smoke.log 2>&1
echo "exit=$?"; rm -rf $R/*_autosmoke
grep -E "Traceback|Error|line [0-9]+," ~/projects/dance_logs/auto_smoke.log | tail -6
grep -E "Episode_Reward/(feet_move_stand|feet_move_rise|foot_impact|squat_template)" ~/projects/dance_logs/auto_smoke.log | tail -4
~/miniforge3/envs/gmr/bin/python -m py_compile ~/dance_win/rl/auto/harness.py ~/dance_win/rl/auto/metrics.py && echo "py ok"
