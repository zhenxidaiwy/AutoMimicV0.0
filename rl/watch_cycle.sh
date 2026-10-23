#!/usr/bin/env bash
# One watch cycle: wait, summarise curves, evaluate any new checkpoint (video + metrics -> W&B).
# Usage: bash watch_cycle.sh <run-name> [sleep_s=1200]
run=$1; sleep ${2:-1200}
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/watch.py $run --every 250
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$run | tail -1)
for ck in $(ls $dir/model_*.pt 2>/dev/null | sort -V); do
  name=$(basename ${ck%.pt})
  [ -f $dir/eval/$name.json ] && continue
  bash ~/dance_win/rl/eval_latest.sh $run $(basename $ck) | grep -E '^\{' | \
    ~/miniforge3/envs/gmr/bin/python -c "import sys,json; r=json.loads(sys.stdin.read()); print('[eval]', '$name', 'completed' if r['completed_clip'] else f\"fell at {r['fell_at_s']} s\", 'body_err_mean', r['body_pos_err_mean_m'], 'joint_err_mean', r['joint_pos_err_mean'])"
done
if grep -q "exit=" ~/projects/dance_logs/train_$run.log; then echo "TRAINING FINISHED: $(grep 'exit=' ~/projects/dance_logs/train_$run.log)"; fi
exit 0
