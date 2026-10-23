#!/usr/bin/env bash
# Re-run GVHMR + retarget for backflip clips whose source is a collage (live video only in a band; GVHMR had tracked
# a static picture). Usage: bash backflip_redo.sh <k>:<y0>:<y1> ...   (band rows from find_band.py, source pixels)
D=~/projects/dance/data; L=~/projects/dance_logs
source ~/miniforge3/etc/profile.d/conda.sh
for spec in "$@"; do
  IFS=: read -r k y0 y1 <<< "$spec"
  id=backflip_$k
  echo "=== $id band $y0-$y1 $(date +%T)"
  rm -rf $D/g1/$id $D/gvhmr/$id; mkdir -p $D/g1/$id
  ffmpeg -loglevel error -y -i $D/clips_raw/$id.mp4 -an \
    -vf "crop=iw:$((y1 - y0 + 1)):0:$y0,fps=30,scale=-2:'min(720,ih)'" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $D/clips/$id.mp4 || { echo "FAILED ffmpeg $id"; continue; }
  conda activate gvhmr
  cd ~/projects/GVHMR
  export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
  python tools/demo/demo.py --video $D/clips/$id.mp4 --output_root $D/gvhmr -s > $D/gvhmr/$id.gvhmr.log 2>&1 \
    || { echo "FAILED gvhmr $id"; continue; }
  conda activate gmr
  export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
  python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4 \
    > $L/retarget_$id.log 2>&1 || { echo "FAILED retarget $id"; continue; }
  Q=~/dance_win/data/qa/$id; mkdir -p $Q
  cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json $Q/ 2>/dev/null
  cp $D/gvhmr/$id/*incam_global_horiz.mp4 $Q/gvhmr.mp4 2>/dev/null || true
  echo "DONE $id"
done
