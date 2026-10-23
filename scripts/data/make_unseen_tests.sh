#!/usr/bin/env bash
# Held-out ("no prior") live-demo test videos: new performers, never-used Bilibili sources (see UNSEEN_README.md).
# Raw sources: ~/projects/dance/data/raw_unseen/av<ID>.mp4 (html5 360p via unseen_download.sh; personal research use only).
# Normalised like live/make_test_videos.sh: fps=30, scale=-2:720, pad=960:720, libx264 crf 18 yuv420p (video only).
# Extra: a centred 4:3 crop first, which is a no-op for portrait sources and keeps landscape sources inside 960 px.
R=~/projects/dance/data/raw_unseen; O=~/projects/dance/live_tests; mkdir -p $O
VF="crop=w='min(iw,ih*4/3)':h=ih,fps=30,scale=-2:720,pad=960:720:(ow-iw)/2:0:black,setsar=1"
cut() {  # out_name raw_id start end
  ffmpeg -loglevel error -y -i $R/$2.mp4 -ss $3 -to $4 -an -vf "$VF" \
    -c:v libx264 -crf 18 -pix_fmt yuv420p $O/$1.mp4 || echo "FAIL $1"
}
#   out             raw id              start  end     performer
cut unseen_sss_1    av117459487038205   3.00   10.50   # boy in navy school uniform, standing on a bed at home
cut unseen_sss_2    av117341190885645   10.30  18.10   # woman, grey top + black shorts, bedroom (shot cuts at 10.17 / 18.20)
cut unseen_sss_3    av117381422713290   1.50   8.50    # woman, cream sweater, blue-curtain studio (landscape -> 4:3 crop)
cut unseen_gxdsm_1  av117381422713290   20.50  29.00   # same blue-curtain woman
cut unseen_gxdsm_2  av117341190885645   57.00  67.30   # same grey-top woman (shot cut at 56.87)
cut unseen_gxdsm_3  av117428046534506   14.40  21.80   # girl (child) in red polka-dot dress, park
# dance switch 闪身步 -> 狗熊哆嗦毛 -> 闪身步, three different performers
ffmpeg -loglevel error -y -i $O/unseen_sss_1.mp4 -i $O/unseen_gxdsm_1.mp4 -i $O/unseen_sss_2.mp4 \
  -filter_complex "[0:v][1:v][2:v]concat=n=3:v=1:a=0[v]" -map "[v]" -c:v libx264 -crf 18 -pix_fmt yuv420p $O/unseen_switch.mp4
for f in $O/unseen_*.mp4; do
  printf "%-22s %s\n" "$(basename $f)" "$(ffprobe -v error -select_streams v:0 -count_frames \
    -show_entries stream=width,height,r_frame_rate,nb_read_frames:format=duration -of csv=p=0 $f | tr '\n' ' ')"
done
