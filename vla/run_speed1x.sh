#!/usr/bin/env bash
# 1x reference for playback rate (rate field did not exist in the earlier 1x runs).
CK=~/dance_win/policies/sss_bda_v1/policy.pt
for clip in gym_sss hoodie_sss; do for s in 0 1 2; do
  bash ~/dance_win/vla/retrieve_loop.sh $clip ret_lead0_s$s $CK --tag _sssexpert_rate
done; done
