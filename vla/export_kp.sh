#!/usr/bin/env bash
# Export keypoints for all clips used by the VLA (train + held-out).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gvhmr
cd ~/projects/GVHMR
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
python ~/dance_win/vla/export_kp.py bda_zhao_sss tonyfu_sss_fast tonyfu_sss_slow tonyfu_sss_single \
  street_sss_a street_sss_b street_sss_c street_sss_d street_sss_e bda2_gxdsm_full \
  gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b 2>&1 | grep -vE "Warning|warn"
