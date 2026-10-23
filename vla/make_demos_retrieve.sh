#!/usr/bin/env bash
# Model-mode (real perception, causal keypoints, 100 ms latency) demo videos with the 闪身步 expert.
CK=~/dance_win/policies/sss_bda_v1/policy.pt
for clip in gym_sss hoodie_sss; do
  bash ~/dance_win/vla/retrieve_loop.sh $clip ret_lead0_s0 $CK --video --tag _sssexpert_vid
  bash ~/dance_win/vla/demo_retrieve.sh ${clip}_model_ret_lead0_s0_lat5_sssexpert_vid \
    "G1 watches an UNSEEN performer (causal keypoints, 100 ms latency) and follows: skill retrieval"
done
