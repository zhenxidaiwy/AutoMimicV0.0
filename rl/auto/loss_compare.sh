#!/usr/bin/env bash
# PPO internals for the first iterations of the C (round-5 lineage) and D (round-4 lineage) resume tests.
T=~/projects/dance_logs/auto_ab
for X in C D; do
  echo "== $X"
  awk -v X=$X '/Learning iteration/{n++} /Mean value[_ ]function loss|Mean value loss/{vl=$NF} /Mean surrogate loss/{sl=$NF} /Mean entropy loss/{el=$NF} /[Kk]l|learning.rate|Learning rate/{ if ($0 ~ /:/) kv[$1]=$NF } /Mean action noise std|Mean action std/{sd=$NF} /Time elapsed/{ if (n <= 6 || n % 10 == 0) { printf "%s iter+%d value_loss %s surrogate %s entropy %s std %s", X, n, vl, sl, el, sd; for (k in kv) printf " %s=%s", k, kv[k]; printf "\n" } }' $T/$X.log
done
grep -aE "^\s+[A-Za-z_ /]+:" $T/C.log | awk -F: '{print $1}' | sort | uniq | head -50
