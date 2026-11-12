#!/usr/bin/env bash
# media_cartwheel.sh: README media for the cartwheel skill (docs/media), same formats as the backflip media:
#   cartwheel_r11_converged.{mp4,gif}  - r11 policy (all gates passed), mjlab eval, first 5 s / 3.8 s, 480x360 GIF
#   cartwheel_evolution.gif            - rounds 1, 2, 3, 7, 11 side by side, 5 x 320x240, 15 fps
#   sim2sim_cartwheel_r11.{mp4,gif}    - mjlab vs native MuJoCo (sim2sim/video_skill.py), 480x240 GIF
#   cartwheel_2_human_to_robot.gif     - mosaicked source clip vs the robot (scripts/data/mosaic/make_media.py)
# Needs: videos/cartwheel_2/auto/rNN_model_*.mp4 (harness evals), data/source_clips_mosaic/cartwheel_2.mp4.
set -e
P=~/dance_win
M=$P/docs/media
T=/tmp/media_cw; mkdir -p $T
V=$P/videos/cartwheel_2/auto
FONT=/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
gif() {  # gif <in> <out> <fps> <scale filter>
  ffmpeg -loglevel error -y -i "$1" -vf "fps=$3,$4,palettegen=max_colors=128:stats_mode=diff" $T/pal.png
  ffmpeg -loglevel error -y -i "$1" -i $T/pal.png -lavfi "fps=$3,$4[x];[x][1:v]paletteuse=dither=bayer:bayer_scale=4:diff_mode=rectangle" -loop 0 "$2"
}
# 1. converged policy (r11 model_12500): cartwheel + 2 s of the hold
ffmpeg -loglevel error -y -t 5 -i $P/policies/cartwheel_r11/flip_auto_model_12500.mp4 -an -c:v libx264 -crf 23 \
  -pix_fmt yuv420p -movflags +faststart $M/cartwheel_r11_converged.mp4
ffmpeg -loglevel error -y -t 3.8 -i $M/cartwheel_r11_converged.mp4 -c:v libx264 -crf 0 $T/conv.mp4
gif $T/conv.mp4 $M/cartwheel_r11_converged.gif 15 "scale=480:360:flags=lanczos"
# 2. evolution: the best checkpoint of rounds 1, 2, 3 (first upright landing), 7 (best score), 11 (all gates)
i=0; IN=""
for rc in "r01_model_1000:round 1" "r02_model_1000:round 2" "r03_model_2998:round 3" "r07_model_8500:round 7" \
          "r11_model_12500:round 11"; do
  f=${rc%%:*}; lab=${rc#*:}
  ffmpeg -loglevel error -y -t 3.8 -i $V/$f.mp4 -vf "fps=15,scale=320:240:flags=lanczos,drawtext=fontfile=$FONT:text='$lab':x=8:y=8:fontsize=18:fontcolor=white" \
    -c:v libx264 -crf 0 $T/evo_$i.mp4
  IN="$IN -i $T/evo_$i.mp4"; i=$((i + 1))
done
ffmpeg -loglevel error -y $IN -filter_complex "hstack=inputs=5" -c:v libx264 -crf 0 $T/evo.mp4
gif $T/evo.mp4 $M/cartwheel_evolution.gif 15 "scale=1600:240"
# 3. sim2sim side by side (mjlab eval trajectory vs native MuJoCo rollout)
(cd $P/sim2sim && MUJOCO_GL=egl python video_skill.py --policy cartwheel_r11 --model cartwheel --out $T/s2s_full.mp4)
ffmpeg -loglevel error -y -t 5 -i $T/s2s_full.mp4 -an -c:v libx264 -crf 23 -pix_fmt yuv420p -movflags +faststart \
  $M/sim2sim_cartwheel_r11.mp4
ffmpeg -loglevel error -y -t 3.8 -i $T/s2s_full.mp4 -c:v libx264 -crf 0 $T/s2s.mp4
gif $T/s2s.mp4 $M/sim2sim_cartwheel_r11.gif 15 "scale=480:240:flags=lanczos"
# 4. internet video -> robot
conda activate gvhmr
python $P/scripts/data/mosaic/make_media.py gif cartwheel 15 128 $M/cartwheel_2_human_to_robot.gif 450 960 4
ls -la $M | grep -i cartwheel
