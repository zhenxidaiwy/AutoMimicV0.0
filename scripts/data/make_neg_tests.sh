#!/usr/bin/env bash
# NEGATIVE live-demo test videos (people NOT doing 闪身步 / 狗熊哆嗦毛), for measuring recogniser false triggers.
# Raw sources: ~/projects/dance/data/raw_neg/av<ID>.mp4 (html5 360p via neg_download.sh; personal research use only).
# Same normalisation as make_unseen_tests.sh: centred 4:3 crop, fps=30, scale=-2:720, pad=960:720, x264 crf 18, video only.
# File names are neutral on purpose; the motion of each file is listed in NEG_README.md.
R=~/projects/dance/data/raw_neg; O=~/projects/dance/live_tests; mkdir -p $O
VF="crop=w='min(iw,ih*4/3)':h=ih,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
cut() {  # out_name raw_id start end
  ffmpeg -loglevel error -y -i $R/$2.mp4 -ss $3 -to $4 -an -vf "$VF" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$1.mp4 || echo "FAIL $1"
}
#   out     raw id              start   end
cut neg_1   av325278019         8.00    17.00    # 科目三 (Subject Three) dance, woman, dance studio
cut neg_2   av668029995         10.00   18.00    # walking in place (原地踏步), man, gym hall
cut neg_3   av47296669          7.00    16.00    # alternating side lunges (侧弓步), man, gym
cut neg_4   av979956852         1.00    10.00    # jumping jacks (开合跳), man, white backdrop
cut neg_5   av114567749312109   108.00  114.00   # standing side-on, talking + arm gestures (posture lesson)
cut neg_6   av117455695450375   147.00  156.00   # 广场舞 solo, woman, virtual backdrop
cut neg_7   av951867735         20.00   29.00    # bodyweight squats (深蹲), woman, white backdrop
cut neg_8   av968635540         27.00   37.00    # warm-up: side step + arm opener, woman
cut neg_9   av117420933122710   98.00   106.00   # 安徽花鼓灯 girls' combination with fan + handkerchief (stage)
for f in $O/neg_*.mp4; do
  printf "%-12s %s\n" "$(basename $f)" "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration -of csv=p=0 $f | tr '\n' ' ')"
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/unseen_cuts.py $f
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/sheet.py $f \
    ~/dance_win/scripts/data/tmp_sheets_neg/out_$(basename $f .mp4).png --every 1 --cols 10 --w 160 --max_tiles 10 >/dev/null
done
