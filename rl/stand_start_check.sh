#!/usr/bin/env bash
# Does the policy keep the canonical stance when it STARTS in it, or drift into its own crooked stance?
# Usage: GETUP_TASK=Dance-Recovery-G1-v7 bash stand_start_check.sh <ckpt>
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA GETUP_TASK=${GETUP_TASK:-Dance-Recovery-G1-v7}
python ~/dance_win/rl/stance_check.py --ckpt $1 --stand_start 2>&1 | \
  grep -E "drift|standing|tilt|template|^joint waist|Error|Traceback|line [0-9]+,"
