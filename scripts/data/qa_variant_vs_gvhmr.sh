#!/usr/bin/env bash
# qa_variant_vs_gvhmr.sh <clip> <variant stem>: render the variant and stack it under the GVHMR render
# -> data/qa/<clip>/qa_<variant>_vs_gvhmr.mp4
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
Q=~/dance_win/data/qa/$1; mkdir -p $Q
python ~/dance_win/scripts/data/render_csv_qa.py $1 $2 $Q/qa_$2.mp4 >/dev/null || exit 1
ffmpeg -loglevel error -y -i $Q/gvhmr.mp4 -i $Q/qa_$2.mp4 -filter_complex \
  "[0:v]scale=-2:480,pad=1100:480:0:0,drawtext=text='GVHMR (human)':x=8:y=8:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6[a];[1:v]scale=-2:480,pad=1100:480:0:0,drawtext=text='G1 $2':x=8:y=8:fontsize=24:fontcolor=yellow:box=1:boxcolor=black@0.6[b];[a][b]vstack" \
  -c:v libx264 -crf 20 -pix_fmt yuv420p $Q/qa_$2_vs_gvhmr.mp4 && echo $Q/qa_$2_vs_gvhmr.mp4
