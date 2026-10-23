#!/usr/bin/env bash
# eval_flip.sh <run-substring> <clip> <variant> [ckpt name]: flip evaluation of a backflip tracker + copy the video
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$1 | tail -1)
ck=${4:-$(ls $dir/model_*.pt | sort -V | tail -1 | xargs basename)}
python ~/dance_win/rl/eval_flip.py --ckpt $dir/$ck --motion ~/projects/dance/dataset/$2/g1_$3_50fps.npz --tag $1_${ck%.pt} \
  --effort-scale ${EFFORT:-1.0} ${KNEE:+--knee-limit $KNEE} 2>&1 | grep -E '^\{'
mkdir -p ~/dance_win/videos/backflip
cp $dir/eval/flip_$1_${ck%.pt}.mp4 ~/dance_win/videos/backflip/ 2>/dev/null
