#!/usr/bin/env bash
# Closed-loop comparison on held-out performers (real video keypoints), 100 ms perception latency for every mode.
# Usage: bash run_closed_loop.sh <tracker_run_substring> [ckpt=latest]
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$1 | tail -1)
ck=${2:-$(ls $dir/model_*.pt | sort -V | tail -1)}; [[ "$ck" = /* ]] || ck=$dir/$ck
echo "tracker: $ck"
CL=~/dance_win/vla/closed_loop.sh
for clip in gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b; do
  bash $CL $clip v1_aux_s0 $ck --mode oracle --latency 5
  for s in 0 1 2; do
    for w in v1_aux_s$s lead5_s$s shadow_s$s; do
      bash $CL $clip $w $ck --latency 5
    done
  done
done
echo CLOSED_LOOP_DONE
