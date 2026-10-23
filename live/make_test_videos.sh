#!/usr/bin/env bash
# Test videos for the live pipeline (held-out performers) + a dance-switch video: 闪身步 -> 狗熊哆嗦毛 -> 闪身步.
# All scaled/padded to 960x720 @30 fps. Written to ~/projects/dance/live_tests (ASCII path, readable from Windows).
O=~/projects/dance/live_tests; C=~/projects/dance/data/clips; mkdir -p $O
VF="fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
for c in gym_sss hoodie_sss bda_ming_gxdsm_a bda_ming_gxdsm_b; do
  ffmpeg -loglevel error -y -i $C/$c.mp4 -vf "$VF" -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$c.mp4
done
ffmpeg -loglevel error -y -i $O/gym_sss.mp4 -i $O/bda_ming_gxdsm_a.mp4 -i $O/hoodie_sss.mp4 \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p $O/switch_test.mp4
ls -la $O
