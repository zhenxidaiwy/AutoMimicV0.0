#!/usr/bin/env bash
# Extract a few frames + frame counts from the dance side-by-side videos into verify_frames/
source ~/miniforge3/etc/profile.d/conda.sh
conda activate unitree_rl_mjlab
cd ~/dance_win/sim2sim
mkdir -p verify_frames
python verify_frames.py
