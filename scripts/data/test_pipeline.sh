#!/usr/bin/env bash
# Smoke test of the full video -> GVHMR -> G1 pipeline on GVHMR's bundled tennis.mp4 (first 4 s).
mkdir -p ~/projects/dance/data/raw
cp -n ~/projects/GVHMR/docs/example_video/tennis.mp4 ~/projects/dance/data/raw/test_tennis.mp4
nvidia-smi --query-gpu=memory.used --format=csv,noheader
time bash ~/dance_win/scripts/data/clip_and_gvhmr.sh test_tennis test_tennis 0 4 static
