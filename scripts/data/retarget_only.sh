#!/usr/bin/env bash
# Re-run only the G1 retarget + QA render for clips whose GVHMR result already exists.
# Usage: bash retarget_only.sh <clip_id> [clip_id ...]
set -e
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
D=~/projects/dance/data
for id in "$@"; do
  python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4 \
    2>&1 | grep -E "^\{|qa video|Error|error" || true
  Q=~/dance_win/data/qa/$id; mkdir -p $Q
  cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json $Q/
  cp $D/gvhmr/$id/*incam_global_horiz.mp4 $Q/gvhmr.mp4 2>/dev/null || true
done
