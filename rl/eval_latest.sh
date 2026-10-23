#!/usr/bin/env bash
# Evaluate the newest checkpoint (or a given one) of a dance run; upload video + metrics to W&B.
# Usage: bash eval_latest.sh <run-name-substring> [model_XXXX.pt]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*$1* | tail -1)
ck=${2:-$(ls $dir/model_*.pt | sort -V | tail -1)}; [[ "$ck" = /* ]] || ck=$dir/$ck
clip=$(echo $1 | sed -E 's/_lock_vlm.*|_ground.*|_raw.*//')
var=$(echo $1 | grep -oE "lock_vlm|lock_heuristic|ground_vlm|ground_heuristic" | head -1)
motion=~/projects/dance/dataset/$clip/g1_${var:-lock_vlm}_50fps.npz
echo "[eval] $ck  motion=$motion"
python ~/dance_win/rl/eval_ckpt.py --ckpt $ck --motion $motion --wandb 2>&1 | grep -E '^\{|^wandb: http|Error|Traceback'
mkdir -p ~/dance_win/videos/$(basename $dir)
cp $dir/eval/$(basename ${ck%.pt}).mp4 ~/dance_win/videos/$(basename $dir)/ 2>/dev/null && echo "copied to videos/$(basename $dir)/"
