#!/usr/bin/env bash
# Download POSITIVE-training candidates (html5 360p via the mobile page) into ~/projects/dance/data/raw_pos_train,
# then 1 s overview sheets + cut detection. Refuses ids in pos_exclude.txt. Personal research use only.
# Usage: bash pos_download.sh <aid|BVid> [...]
PY=~/miniforge3/envs/gmr/bin/python
RAW=~/projects/dance/data/raw_pos_train; SH=~/dance_win/scripts/data/tmp_sheets_pos; mkdir -p $RAW $SH
EX=~/projects/dance/data/search/pos_exclude.txt
IDS=""
for x in "$@"; do
  y=${x#av}
  if grep -qx "$y" $EX; then echo "EXCLUDED $x"; else IDS="$IDS $y"; fi
done
F=~/dance_win/scripts/data/tmp_pos_fetch.py
sed 's/info\["duration"\] > 300/info["duration"] > int(os.environ.get("MAXDUR", 300))/' \
  ~/dance_win/scripts/data/unseen_fetch.py > $F
$PY -I $F get $RAW $IDS
for v in $RAW/av*.mp4; do
  b=$(basename $v .mp4)
  [ -f $SH/$b.png ] && continue
  grep -qx "${b#av}" $EX && { echo "EXCLUDED after resolve: $b"; rm -f $RAW/$b.mp4 $RAW/$b.meta.json; continue; }
  $PY -I ~/dance_win/scripts/data/sheet.py $v $SH/$b.png --every 1 --cols 10 --w 96 --max_tiles 80
  $PY -I ~/dance_win/scripts/data/unseen_cuts.py $v
done
