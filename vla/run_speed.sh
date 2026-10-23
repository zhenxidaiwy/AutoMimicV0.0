#!/usr/bin/env bash
# Speed test: human video at 0.5x (and 1x reference), 闪身步 expert, model mode (3 seeds) + oracle alignment.
CK=~/dance_win/policies/sss_bda_v1/policy.pt
for clip in gym_sss hoodie_sss; do
  bash ~/dance_win/vla/retrieve_loop.sh $clip - $CK --mode oracle_align --speed 0.5 --tag _sssexpert
  for s in 0 1 2; do
    bash ~/dance_win/vla/retrieve_loop.sh $clip ret_lead0_s$s $CK --speed 0.5 --tag _sssexpert
  done
done
bash ~/dance_win/vla/retrieve_loop.sh gym_sss ret_lead0_s0 $CK --speed 0.5 --video --tag _sssexpert_vid
bash ~/dance_win/vla/demo_retrieve.sh gym_sss_model_ret_lead0_s0_lat5_x0.5_sssexpert_vid \
  "Human video at 0.5x speed: does G1 slow down? (unseen performer, causal keypoints)"
