#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gvhmr
cd ~/projects/GVHMR
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
python ~/dance_win/vla/causal_kp.py gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b 2>&1 | grep -E "causal vs|Error|Traceback|line [0-9]+,"
