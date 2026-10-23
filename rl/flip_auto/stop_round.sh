#!/usr/bin/env bash
# stop_round.sh K tag: stop the running harness round K (started by me) and rename its log / run dir with _aborted_<tag>
pkill -f "harnes[s].py --mode"; sleep 2; pkill -f "train_dance.py.*flipaut[o]_r"; sleep 3
pgrep -af "harnes[s].py|train_danc[e].py" || echo "stopped"
K=$(printf %02d $1)
mv ~/projects/dance_logs/train_flipauto_r$K.log ~/projects/dance_logs/train_flipauto_r${K}_aborted_$2.log 2>/dev/null
for d in ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_flipauto_r$K; do
  [ -d "$d" ] && mv "$d" "${d}_aborted_$2" && echo "moved $d"
done
