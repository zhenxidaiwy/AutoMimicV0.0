#!/bin/bash
# CPU-only smoke test of the world-model code (safe while a training run holds the GPU)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export CUDA_VISIBLE_DEVICES=
cd ~/dance_win/rl/wm || exit 1
rm -rf /tmp/wm_smoke
python smoke_test.py /tmp/wm_smoke
