#!/usr/bin/env bash
# Model-mode closed loop on held-out 闪身步 performers with the 闪身步 expert (until the one-brain tracker is ready).
CK=~/dance_win/policies/sss_bda_v1/policy.pt
for clip in gym_sss hoodie_sss; do
  bash ~/dance_win/vla/retrieve_loop.sh $clip - $CK --mode oracle_align --tag _sssexpert
  for s in 0 1 2; do
    bash ~/dance_win/vla/retrieve_loop.sh $clip ret_lead0_s$s $CK --tag _sssexpert
  done
done
