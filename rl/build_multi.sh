#!/usr/bin/env bash
# Build the multi-motion training file for the generalist tracker (train split only; held-out performers excluded).
# Held out (never seen by tracker or high-level): gym_sss, hoodie_sss (闪身步), bda_ming_gxdsm_a/b (狗熊哆嗦毛).
mkdir -p ~/projects/dance/multi
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/build_multi.py ~/projects/dance/multi/train_v1.npz \
  bda_zhao_sss tonyfu_sss_fast tonyfu_sss_slow tonyfu_sss_single \
  street_sss_a street_sss_b street_sss_c street_sss_d street_sss_e bda2_gxdsm_full
