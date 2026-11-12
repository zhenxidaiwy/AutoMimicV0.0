#!/usr/bin/env bash
# clip_gvhmr_retarget.sh <clip id> <source video> <start s> <end s> <crop w:h:x:y>: generic single-clip front end of
# the pipeline (any skill): cut + crop + 30 fps -> GVHMR -> GMR retarget (G1) -> QA copies.
# Writes data/clips_raw/<id>.mp4 (uncropped cut), data/clips/<id>.mp4 (GVHMR input), data/gvhmr/<id>/,
# data/g1/<id>/ (g1.csv, qa.mp4, metrics.json) and ~/dance_win/data/qa/<id>/ (local only, gitignored).
id=$1; src=$2; ss=$3; to=$4; crop=$5
D=~/projects/dance/data; L=~/projects/dance_logs
source ~/miniforge3/etc/profile.d/conda.sh
mkdir -p $D/clips_raw $D/clips $D/gvhmr $D/g1/$id
echo "=== $id: $src [$ss, $to] crop $crop $(date +%T)"
ffmpeg -loglevel error -y -ss $ss -to $to -i "$src" -an -c:v libx264 -crf 16 -pix_fmt yuv420p $D/clips_raw/$id.mp4 || exit 1
ffmpeg -loglevel error -y -i $D/clips_raw/$id.mp4 -an -vf "crop=$crop,fps=30,scale=-2:'min(720,ih)'" \
  -c:v libx264 -crf 18 -pix_fmt yuv420p $D/clips/$id.mp4 || exit 1
ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=width,height,nb_read_frames -of csv=p=0 $D/clips/$id.mp4
rm -rf $D/gvhmr/$id
conda activate gvhmr
cd ~/projects/GVHMR || exit 1
export TORCH_FORCE_NO_WEIGHTS_ONLY_LOAD=1
python tools/demo/demo.py --video $D/clips/$id.mp4 --output_root $D/gvhmr -s > $D/gvhmr/$id.gvhmr.log 2>&1 \
  || { echo "FAILED gvhmr $id"; tail -5 $D/gvhmr/$id.gvhmr.log; exit 1; }
conda activate gmr
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
python ~/dance_win/scripts/data/retarget_headless.py $D/gvhmr/$id/hmr4d_results.pt $D/g1/$id --clip $D/clips/$id.mp4 \
  > $L/retarget_$id.log 2>&1 || { echo "FAILED retarget $id"; tail -5 $L/retarget_$id.log; exit 1; }
Q=~/dance_win/data/qa/$id; mkdir -p $Q
cp $D/g1/$id/qa.mp4 $D/g1/$id/metrics.json $Q/ 2>/dev/null
cp $D/gvhmr/$id/*incam_global_horiz.mp4 $Q/gvhmr.mp4 2>/dev/null || true
echo "DONE $id $(date +%T)"; cat $D/g1/$id/metrics.json 2>/dev/null | head -c 600; echo
