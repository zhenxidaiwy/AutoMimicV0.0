#!/usr/bin/env bash
# canon_v1: the two canonical high-quality clips (闪身步 = BDA Zhao, 狗熊哆嗦毛 = BDA full demo), equal weight.
~/miniforge3/envs/gmr/bin/python ~/dance_win/rl/build_multi.py ~/projects/dance/multi/canon_v1.npz --balance clip \
  bda_zhao_sss bda2_gxdsm_full
