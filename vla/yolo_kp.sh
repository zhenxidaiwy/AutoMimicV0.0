#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gvhmr
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1  # yolov8n-pose.pt from the official ultralytics GitHub release
python ~/dance_win/vla/yolo_kp.py bda_zhao_sss tonyfu_sss_fast tonyfu_sss_slow tonyfu_sss_single street_sss_a \
  street_sss_b street_sss_c street_sss_d street_sss_e bda2_gxdsm_full gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b \
  2>&1 | grep -E "YOLO vs|Error|Traceback|line [0-9]+,"
