#!/usr/bin/env bash
# Wait for the running get-up training to finish, evaluate it, then resume from its latest checkpoint for N more
# iterations (total = first run + N). Usage: bash chain_getup.sh [more_iters=2500]
more=${1:-2500}
while pgrep -f train_getup.py > /dev/null; do sleep 30; done
d=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/* | tail -1)
echo "[chain] first run finished: $(basename $d) $(date)"
bash ~/dance_win/rl/eval_getup.sh --video
echo "[chain] resuming $(basename $d) for $more more iterations $(date)"
RESUME=$(basename $d) bash ~/dance_win/rl/train_getup.sh 2048 $more
echo "[chain] resume finished $(date)"
bash ~/dance_win/rl/eval_getup.sh --video
