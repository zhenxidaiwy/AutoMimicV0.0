#!/usr/bin/env bash
# High-resolution (960x720) evaluation of one checkpoint + every-frame sheet of the flight window.
# Usage: bash peek_hd.sh <run dir name> <ckpt> [first=92] [last=131]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1
DS=~/projects/dance/dataset/backflip_3
python ~/dance_win/rl/eval_flip.py --ckpt $dir/$2 --motion $DS/g1_ballistic_50fps.npz --tag hd_${2%.pt} \
  --knee-limit 120 --labels $DS/labels_50fps.npz --size 960 720 2>&1 | grep -E '^\{'
out=~/dance_win/videos/backflip/auto; mkdir -p $out
cp $dir/eval/flip_hd_${2%.pt}.mp4 $out/hd_$1_${2%.pt}.mp4
a=${3:-92}; b=${4:-131}
bash ~/dance_win/scripts/data/sheet_grid.sh $out/hd_$1_${2%.pt}.mp4 $out/hd_$1_${2%.pt}_flight.jpg $a $b 1 8
