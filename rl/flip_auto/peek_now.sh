#!/usr/bin/env bash
# Evaluate one checkpoint of a harness round right now (from standing, EDU knee limit) and build a side-by-side
# video with the human clip. Usage: bash peek_now.sh <round dir substring> <ckpt>
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*$1 | tail -1)
DS=~/projects/dance/dataset/backflip_3
python ~/dance_win/rl/eval_flip.py --ckpt $dir/$2 --motion $DS/g1_ballistic_50fps.npz --tag peek_${2%.pt} \
  --knee-limit 120 --labels $DS/labels_50fps.npz 2>&1 | grep -E '^\{'
out=~/dance_win/videos/backflip/auto
mkdir -p $out
cp $dir/eval/flip_peek_${2%.pt}.mp4 $out/now_$1_${2%.pt}.mp4
bash ~/dance_win/scripts/data/flip_compare.sh $out/now_$1_${2%.pt}_compare.mp4 ~/projects/dance/data/clips/backflip_3.mp4 \
  "robot now=$out/now_$1_${2%.pt}.mp4" > /dev/null
bash ~/dance_win/scripts/data/peek.sh $out/now_$1_${2%.pt}.mp4 $out/now_$1_${2%.pt}_frames.jpg 40 55 62 68 74 82 95 115
