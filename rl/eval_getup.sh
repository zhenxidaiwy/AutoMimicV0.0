#!/usr/bin/env bash
# Usage: [CKPT=path] bash eval_getup.sh [extra args, e.g. --video]   (default: latest get-up checkpoint)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/g1_recovery/*${RUN_FILTER} | tail -1)
ck=${CKPT:-$(ls $dir/model_*.pt | sort -V | tail -1)}
echo "ckpt $ck"
python ~/dance_win/rl/eval_getup.py --ckpt $ck --n 64 "$@" 2>&1 | grep -E "overall|final|max pelvis|  [a-z]|unclassified|video:|Error|Traceback|line [0-9]+,"
if [ -f $(dirname $ck)/getup_eval.mp4 ]; then
  mkdir -p ~/dance_win/videos/getup
  cp $(dirname $ck)/getup_eval.mp4 ~/dance_win/videos/getup/$(basename $(dirname $ck))_$(basename ${ck%.pt}).mp4
  ~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/sheet.py $(dirname $ck)/getup_eval.mp4 \
    ~/dance_win/videos/getup/latest_sheet.png --every 1 --cols 5 --w 360
fi
