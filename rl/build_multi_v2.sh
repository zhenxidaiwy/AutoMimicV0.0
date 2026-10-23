#!/usr/bin/env bash
# train_v2: same 10 training clips, every clip gets equal sampling mass (short clips were under-trained in v1).
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/build_multi.py ~/projects/dance/multi/train_v2.npz --balance clip \
  bda_zhao_sss tonyfu_sss_fast tonyfu_sss_slow tonyfu_sss_single \
  street_sss_a street_sss_b street_sss_c street_sss_d street_sss_e bda2_gxdsm_full
