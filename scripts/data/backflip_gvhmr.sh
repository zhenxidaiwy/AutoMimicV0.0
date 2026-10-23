#!/usr/bin/env bash
# Backflip capability probe: GVHMR (static camera) + headless G1 retarget for the already-cut backflip clips.
# Clips come from make_backflip_clips.sh (source resolution, 30 fps); like clip_and_gvhmr.sh they are scaled to <=720p.
# Usage: bash backflip_gvhmr.sh [k ...]  (default 1..10)   Log: ~/projects/dance_logs/backflip_gvhmr.log
D=~/projects/dance/data; L=~/projects/dance_logs; mkdir -p $L
source ~/miniforge3/etc/profile.d/conda.sh
ks="$*"; [ -z "$ks" ] && ks="1 2 3 4 5 6 7 8 9 10"
for k in $ks; do
  id=backflip_$k
  [ -f $D/g1/$id/g1.csv ] && { echo "skip $id (done)"; continue; }
  echo "=== $id $(date +%T)"
  mkdir -p $D/clips_raw $D/gvhmr $D/g1/$id
  [ -f $D/clips_raw/$id.mp4 ] || mv $D/clips/$id.mp4 $D/clips_raw/$id.mp4
  ffmpeg -loglevel error -y -i $D/clips_raw/$id.mp4 -an -vf "fps=30,scale=-2:'min(720,ih)'" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $D/clips/$id.mp4 || { echo "FAILED ffmpeg $id"; continue; }
  conda activate gvhmr
  cd ~/projects/GVHMR
  export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
  python tools/demo/demo.py --video $D/clips/$id.mp4 --output_root $D/gvhmr -s > $D/gvhmr/$id.gvhmr.log 2>&1 \
    || { echo "FAILED gvhmr $id"; grep -E "Error|error" $D/gvhmr/$id.gvhmr.log | tail -3; continue; }
  conda activate gmr
  export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
  python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4 \
    > $L/retarget_$id.log 2>&1 || { echo "FAILED retarget $id"; tail -3 $L/retarget_$id.log; continue; }
  Q=~/dance_win/data/qa/$id; mkdir -p $Q
  cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json $Q/ 2>/dev/null
  cp $D/gvhmr/$id/*incam_global_horiz.mp4 $Q/gvhmr.mp4 2>/dev/null || true
  echo "DONE $id"
done
echo ALL_DONE
