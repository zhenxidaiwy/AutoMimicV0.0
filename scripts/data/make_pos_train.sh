#!/usr/bin/env bash
# POSITIVE training clips (new performers) for the dance recogniser: 狗熊哆嗦毛 (gxdsm_k) and 闪身步 (sss_k).
# Raw sources: ~/projects/dance/data/raw_pos_train/av<ID>.mp4 (html5 360p via pos_download.sh; personal research use only).
# No source av id is in pos_exclude.txt (raw_unseen, raw_neg, raw_neg2, clips.tsv, live_tests READMEs).
# Same normalisation as the live tests: centred 4:3 crop, fps=30, scale=-2:720, pad=960:720, x264 crf 18, video only.
# Optional 5th arg = extra filter placed BEFORE the normalisation (used to cut off a picture-in-picture band).
R=~/projects/dance/data/raw_pos_train; O=~/projects/dance/data/pos_train; mkdir -p $O
SH=~/dance_win/scripts/data/tmp_sheets_pos; mkdir -p $SH
VF="crop=w='min(iw,ih*4/3)':h=ih,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
cut() {  # out_name raw_id start end [pre_filter]
  local vf="$VF"; [ -n "$5" ] && vf="$5,$VF"
  ffmpeg -loglevel error -y -i $R/$2.mp4 -ss $3 -to $4 -an -vf "$vf" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$1.mp4 || echo "FAIL $1"
}
PIP="crop=iw:ih-176:0:176"   # av117421637633984: drop the top 176 px (uploader caption + inset playing the BDA reference video)
#   out       raw id              start  end
cut gxdsm_1  av117323675600986   24.80  31.00          # woman, bob hair, black sleeveless jumpsuit, white curtain
cut gxdsm_2  av117344059853267   28.90  35.20          # cosplayer, long black wig, school uniform + grey jacket, pink backdrop
cut gxdsm_3  av117444957963125    5.60   9.60          # blonde woman, black top/trousers, lawn in front of a castle
cut gxdsm_4  av117424842148656    5.90  12.00          # woman, white shirt + suspenders + black shorts, white studio
cut gxdsm_5  av117472506220761    8.80  13.90          # woman, light-green sweatsuit, courtyard at night
cut gxdsm_6  av117421637633984    8.30  12.00  "$PIP"  # young man, plaid overshirt + grey sweatpants, practice room
cut gxdsm_7  av117372161688659    5.60   9.60          # woman, beige top + wide trousers, public square
cut sss_1    av117323675600986    1.60   7.00          # same woman as gxdsm_1
cut sss_2    av117472506220761    0.30   5.30          # same woman as gxdsm_5
cut sss_3    av117421637633984    2.70   5.90  "$PIP"  # same man as gxdsm_6
cut sss_4    av117444957963125    1.80   5.20          # same woman as gxdsm_3
cut sss_5    av117424842148656    0.00   3.00          # same woman as gxdsm_4
for f in $O/gxdsm_*.mp4 $O/sss_*.mp4; do
  n=$(basename $f .mp4)
  printf "%-10s %s\n" "$n" "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration -of csv=p=0 $f | tr '\n' ' ')"
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/unseen_cuts.py $f
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/sheet.py $f \
    $SH/out_$n.png --every 0.33 --cols 10 --w 96 --max_tiles 40 >/dev/null
done
