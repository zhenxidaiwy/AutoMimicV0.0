#!/usr/bin/env bash
# Usage: bash demo_getup.sh <ckpt> <name> ["title"]   -> ~/dance_win/videos/getup/<name>.mp4 (+ _sheet.png)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
out=~/dance_win/videos/getup/$2.mp4
python ~/dance_win/rl/demo_getup.py --ckpt $1 --out $out --title "${3:-G1 get-up policy}" 2>&1 | \
  grep -E "stood up at|video:|Error|Traceback|line [0-9]+,"
~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/sheet.py $out ${out%.mp4}_sheet.png --every 0.5 --cols 4 --w 640 --max_tiles 12
