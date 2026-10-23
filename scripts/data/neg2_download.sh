#!/usr/bin/env bash
# Download negative batch-2 candidates (html5 360p via the mobile page) into ~/projects/dance/data/raw_neg2,
# then 1 s overview sheets + cut detection. Refuses ids in neg2_exclude.txt. Personal research use only.
# Usage: bash neg2_download.sh <aid|BVid> [...]
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_neg2; SH=~/dance_win/scripts/data/tmp_sheets_neg2; mkdir -p $RAW $SH
EX=~/projects/dance/data/search/neg2_exclude.txt
IDS=""
for x in "$@"; do
  y=${x#av}
  if grep -qx "$y" $EX; then echo "EXCLUDED $x"; else IDS="$IDS $y"; fi
done
# same fetcher, but the 300 s length cap is configurable (MAXDUR, default 300) for long 太极/八段锦 videos
F=~/dance_win/scripts/data/tmp_neg2_fetch.py
sed 's/info\["duration"\] > 300/info["duration"] > int(os.environ.get("MAXDUR", 300))/' \
  ~/dance_win/scripts/data/unseen_fetch.py > $F
$PY -I $F get $RAW $IDS
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  grep -qx "${b#av}" $EX && { echo "EXCLUDED after resolve: $b"; rm -f $RAW/$b.mp4 $RAW/$b.meta.json; continue; }
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 10 --w 128 --max_tiles 80
  $PY -I ~/dance_win/scripts/data/unseen_cuts.py $v
done
