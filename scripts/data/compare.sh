#!/usr/bin/env bash
# Usage: bash compare.sh <clip_id> <variant> [...]   -> side-by-side mp4 + a contact sheet png of it
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
P=~/miniforge3/envs/gmr/bin/python
out=$($P ~/dance_win/scripts/data/render_compare.py "$@" --src | tail -1)
$P ~/dance_win/scripts/data/sheet.py $out ${out%.mp4}.png --every 0.2 --cols 4 --w 600 --max_tiles 40
