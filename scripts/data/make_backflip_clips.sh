#!/usr/bin/env bash
# Standing-backflip training clips for the video->robot pipeline (same pipeline as 闪身步).
# Raw sources: ~/projects/dance/data/raw_backflip/av<ID>.mp4 (html5 360p/1080p via bf_download.sh; personal research only).
# Clips are NOT normalised: source resolution kept, only resampled to 30 fps, video only. See BACKFLIP_README.md.
R=~/projects/dance/data/raw_backflip; O=~/projects/dance/data/clips; mkdir -p $O
cut() {  # clip_id raw_id start end
  ffmpeg -loglevel error -y -i $R/$2.mp4 -ss $3 -to $4 -an -vf "fps=30" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$1.mp4 || echo "FAIL $1"
}
#   clip         raw id              start   end
cut backflip_1   av75680591          23.00   25.90   # wushu athlete, black, grass field, front view
cut backflip_2   av75680591          29.00   31.75   # same athlete, side view
cut backflip_3   av75680591          35.20   38.25   # same athlete, third take
cut backflip_4   av116460269603942   3.50    6.90    # young man, white T-shirt + grey trousers, tricking gym
cut backflip_5   av116460269603942   8.50    11.30   # same man, 2nd take
cut backflip_6   av116460269603942   12.00   15.20   # same man, 3rd take
cut backflip_7   av117438112863924   25.60   27.85   # man, purple T-shirt, tricking gym floor mats
cut backflip_8   av116641228784719   15.35   18.65   # man, white tee + grey trousers, gym (lands on crash mat)
cut backflip_9   av115505847472177   62.90   65.85   # heavy-set man, grey vest + black shorts, air-floor
cut backflip_10  av233376646         1.90    4.40    # cheerleader, navy uniform, athletics track
P=~/miniforge3/envs/gmr/bin/python
for k in $(seq 1 10); do
  f=$O/backflip_$k.mp4
  printf "%-16s %s\n" backflip_$k "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames -of csv=p=0 $f)"
  $P -I ~/dance_win/scripts/data/unseen_cuts.py $f | sed 's/^.*cuts:/  cuts:/'
done
