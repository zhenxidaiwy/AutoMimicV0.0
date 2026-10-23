#!/usr/bin/env bash
# First iterations of a harness round: when does it go wrong? Usage: bash early_curve.sh K
L=~/projects/dance_logs/auto/r$(printf "%02d" $1)/train.log
awk '
/Learning iteration/ { match($0, /[0-9]+\/[0-9]+/); split(substr($0, RSTART, RLENGTH), a, "/"); cur = a[1]; n++ }
/Mean reward:/ { mr = $3 }
/Episode_Reward\/stand_up:/ { su = $2 }
/Episode_Reward\/arm_still:/ { ar = $2 }
/Episode_Reward\/feet_move_stand:/ { fm = $2 }
/Episode_Reward\/torso_still:/ { ts = $2 }
/Episode_Reward\/floor_stall:/ { fs = $2 }
/Mean action noise std|Mean action std/ { sd = $NF }
/Time elapsed/ { if (n <= 12 || n % 25 == 0) printf "it %s  reward %8s  stand_up %s  arm %s  feet %s  torso %s  stall %s  std %s\n", cur, mr, su, ar, fm, ts, fs, sd }
' $L | head -40
