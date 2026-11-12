#!/usr/bin/env bash
# compare_train.sh A B [n_iters]: mean of selected Episode_Reward terms over the last n logged iterations of round A
# vs the same number of iterations into round B (training-time trend, not an evaluation)
A=$(printf %02d $1); B=$(printf %02d $2); N=${3:-200}
LA=~/projects/dance_logs/train_flipauto_r$A.log; LB=~/projects/dance_logs/train_flipauto_r$B.log
done_b=$(grep -c 'Learning iteration' $LB)
for t in flip_stand_quiet flip_stand_still flip_land_balance flip_spin "Mean episode length"; do
  a=$(grep -E "$t" $LA | sed -n "1,${done_b}p" | tail -n $N | awk '{s+=$NF; n++} END {if (n) printf "%.4f", s/n}')
  b=$(grep -E "$t" $LB | tail -n $N | awk '{s+=$NF; n++} END {if (n) printf "%.4f", s/n}')
  printf "%-22s r%s %8s   r%s %8s\n" "$t" $A "$a" $B "$b"
done
echo "(r$B iterations so far: $done_b; both averaged over iterations $((done_b-N))..$done_b of their round)"
