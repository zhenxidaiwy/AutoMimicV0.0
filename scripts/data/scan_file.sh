#!/usr/bin/env bash
# scan_file.sh <video> <every s> <out.jpg> [start s] [dur s]: probe a video and make a timestamped contact sheet
# (one frame every N s) of the whole video or of [start, start+dur]
v=$1; e=$2; o=$3; ss=${4:-0}; t=${5:-}
ffprobe -v error -show_entries format=duration:stream=width,height,r_frame_rate,nb_frames -of compact "$v" | grep -v audio
dur=${t:-$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$v")}
n=$(python3 -c "print(int(float('$dur') / $e) + 1)")
rows=$(( (n + 9) / 10 ))
ffmpeg -loglevel error -y -ss "$ss" ${t:+-t $t} -i "$v" -vf "fps=1/$e,drawtext=text='%{pts\:hms}':x=4:y=4:fontsize=28:fontcolor=yellow:box=1:boxcolor=black@0.7,scale=-2:200,tile=10x$rows" -frames:v 1 "$o"
echo "sheet $o: $n frames from $ss s (pts in the sheet start at 0 = $ss s)"
