#!/usr/bin/env bash
# Cut a segment, normalise to 30 fps / <=720p, run GVHMR, then retarget to G1 headless.
# Usage: bash clip_and_gvhmr.sh <bvid> <clip_id> <start_s> <end_s> <static|moving>
# GVHMR's demo assumes 30 fps input, hence the fps conversion. torch>=2.6 needs weights_only=False loads.
set -eo pipefail
bv=$1; id=$2; ss=$3; to=$4; cam=$5
D=~/projects/dance/data; mkdir -p $D/clips $D/gvhmr $D/g1/$id
ffmpeg -loglevel error -y -ss $ss -to $to -i $D/raw/$bv.mp4 -an \
  -vf "fps=30,scale=-2:'min(720,ih)'" -c:v libx264 -crf 18 -pix_fmt yuv420p $D/clips/$id.mp4
# refuse clips that contain a hard/jump cut: GVHMR would treat it as continuous motion (root teleports)
cuts=$(~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/detect_cuts.py $D/clips/$id.mp4)
echo "$cuts"
echo "$cuts" | grep -q "cuts: \[\]" || { echo "ABORT $id: cut detected, split the clip"; exit 3; }

source ~/miniforge3/etc/profile.d/conda.sh
conda activate gvhmr
cd ~/projects/GVHMR
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
flag=""; [ "$cam" = "static" ] && flag="-s"
python tools/demo/demo.py --video $D/clips/$id.mp4 --output_root $D/gvhmr $flag > $D/gvhmr/$id.gvhmr.log 2>&1 \
  || { echo "GVHMR failed for $id, see $D/gvhmr/$id.gvhmr.log"; grep -E "Error|error" $D/gvhmr/$id.gvhmr.log | tail -5; exit 4; }

conda activate gmr
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4
# copy QA artefacts to the Windows side for viewing
Q=~/dance_win/data/qa/$id; mkdir -p $Q
cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json $Q/
cp $D/gvhmr/$id/*incam_global_horiz.mp4 $Q/gvhmr.mp4 2>/dev/null || true
echo "DONE $id"
