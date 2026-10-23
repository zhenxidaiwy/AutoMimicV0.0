#!/usr/bin/env bash
# Training-curve diagnosis of a harness round: key reward terms every ~100 iterations.
# Usage: bash diag_round.sh K
L=~/projects/dance_logs/auto/r$(printf "%02d" $1)/train.log
awk '
/Learning iteration/ { match($0, /[0-9]+\/[0-9]+/); it = substr($0, RSTART, RLENGTH); split(it, a, "/"); cur = a[1] }
/Mean reward:/ { mr = $3 }
/Mean episode length:/ { el = $4 }
/Episode_Reward\/stand_up:/ { su = $2 }
/Episode_Reward\/squat_template:/ { sq = $2 }
/Episode_Reward\/stand_template:/ { stt = $2 }
/Episode_Reward\/feet_move_rise:/ { fr = $2 }
/Episode_Reward\/feet_spread:/ { fs = $2 }
/Episode_Reward\/rise_schedule:/ { rs = $2 }
/Mean action noise std|Mean action std/ { sd = $NF }
/Time elapsed/ { if (cur % 100 == 0 || cur % 100 == 99) printf "it %s  reward %s  stand_up %s  squat %s  stand_tmpl %s  feet_rise %s  spread %s  sched %s  std %s\n", cur, mr, su, sq, stt, fr, fs, rs, sd }
' $L
