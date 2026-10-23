#!/usr/bin/env bash
# NEGATIVE live-demo test videos, batch 2 (held-out; people NOT doing 闪身步 / 狗熊哆嗦毛).
# Raw sources: ~/projects/dance/data/raw_neg2/av<ID>.mp4 (html5 360p via neg2_download.sh; personal research use only).
# Every source av id differs from batch 1 (raw_neg), raw_unseen and data/annotations/clips.tsv (neg2_exclude.sh).
# Same normalisation as make_neg_tests.sh: centred 4:3 crop, fps=30, scale=-2:720, pad=960:720, x264 crf 18, video only.
# File names are neutral on purpose; the motion of each file is listed in NEG2_README.md.
R=~/projects/dance/data/raw_neg2; O=~/projects/dance/live_tests; mkdir -p $O
SH=~/dance_win/scripts/data/tmp_sheets_neg2; mkdir -p $SH
VF="crop=w='min(iw,ih*4/3)':h=ih,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
cut() {  # out_name raw_id start end
  ffmpeg -loglevel error -y -i $R/$2.mp4 -ss $3 -to $4 -an -vf "$VF" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$1.mp4 || echo "FAIL $1"
}
#   out     raw id              start   end
cut neg_10  av929113809         24.00   33.00    # K-pop cover (BLACKPINK Lovesick Girls), woman, practice room
cut neg_11  av980445915         60.00   69.00    # hip-hop bounce freestyle, man, practice room (portrait)
cut neg_12  av115655483332578   40.00   49.00    # 健美操 (aerobics) basic routine, girl, curtain stage
cut neg_13  av847448728         120.00  129.00   # 24式太极拳 front demo, woman, studio
cut neg_14  av949268496         2.00    11.00    # shadow boxing 3-punch combos, man, studio (motion-actor reference)
cut neg_15  av221839081         30.00   39.00    # yoga sequence (step out, arms up, warrior lunge), woman, park
cut neg_16  av449913934         20.00   29.00    # jogging in place, woman, white backdrop
cut neg_17  av116168832584860   46.00   55.00    # cha-cha basic steps, woman, back view (portrait)
cut neg_18  av117443699737792   2.00    11.00    # cheerful greeting / waving with leg kicks, woman, white room
cut neg_19  av114574862844188   40.00   49.00    # walking around + turning, man, dark studio
cut neg_20  av838244221         50.00   59.00    # 鬼步舞 (shuffle) solo, woman, outdoor road
cut neg_21  av784695080         46.50   55.50    # 挖呀挖 (花园种花) meme dance, woman, green-screen backdrop
for n in 10 11 12 13 14 15 16 17 18 19 20 21; do
  f=$O/neg_$n.mp4
  printf "%-12s %s\n" "$(basename $f)" "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration -of csv=p=0 $f | tr '\n' ' ')"
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/unseen_cuts.py $f
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/sheet.py $f \
    $SH/out_neg_$n.png --every 1 --cols 10 --w 120 --max_tiles 10 >/dev/null
done
