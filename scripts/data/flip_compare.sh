#!/usr/bin/env bash
# Side-by-side backflip comparison: source human clip | robot videos (each scaled to 360 px high, 30 fps, labelled).
# Usage: bash flip_compare.sh <out.mp4> <human.mp4> <label1>=<robot1.mp4> [<label2>=<robot2.mp4> ...]
out=$1; human=$2; shift 2
inputs=(-i "$human"); filt="[0:v]fps=30,scale=-2:360,drawtext=text='human video':x=10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.5,setpts=PTS-STARTPTS[v0];"
n=1
for spec in "$@"; do
  lab=${spec%%=*}; f=${spec#*=}
  inputs+=(-i "$f")
  filt+="[$n:v]fps=30,scale=-2:360,drawtext=text='$lab':x=10:y=10:fontsize=22:fontcolor=white:box=1:boxcolor=black@0.5,setpts=PTS-STARTPTS[v$n];"
  n=$((n + 1))
done
for i in $(seq 0 $((n - 1))); do filt+="[v$i]"; done
filt+="hstack=inputs=$n:shortest=0[o]"
ffmpeg -loglevel error -y "${inputs[@]}" -filter_complex "$filt" -map "[o]" -c:v libx264 -crf 20 -pix_fmt yuv420p "$out"
ls -la "$out"
