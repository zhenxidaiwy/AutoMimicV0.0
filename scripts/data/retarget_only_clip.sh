#!/usr/bin/env bash
# retarget_only_clip.sh <clip id>: re-run GMR retargeting (+ QA copy) on an existing GVHMR result
id=$1
D=~/projects/dance/data
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
shift
python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4 "$@" \
  2>&1 | grep -E "escape|Error|Traceback|frames"
mkdir -p ~/dance_win/data/qa/$id; cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json ~/dance_win/data/qa/$id/
