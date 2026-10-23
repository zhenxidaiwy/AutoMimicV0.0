#!/usr/bin/env bash
# Download every searched candidate (<=300 s, video only, <=720p) with its info.json, then a 1 s contact sheet.
# Resumable: skips ids already downloaded. Raw videos are for personal research only (never published).
pkill -f search_bili.py 2>/dev/null
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
RAW=~/projects/dance/data/raw; SHEET=~/dance_win/data/qa/sheets; mkdir -p $RAW $SHEET
IDS=$(python -c "import json,os; print(' '.join(json.load(open(os.path.expanduser('~/projects/dance/data/search/ids.json')))))")
n=0
for aid in $IDS; do
  n=$((n+1))
  ls $RAW/av$aid.* >/dev/null 2>&1 && continue
  python -m yt_dlp -q --no-warnings --no-progress --match-filter "duration<=300" --write-info-json \
    -f "bv*[height<=720][vcodec^=avc]/bv*[height<=720]/bv*" --remux-video mp4 \
    -o "$RAW/av$aid.%(ext)s" "https://www.bilibili.com/video/av$aid" || echo "FAIL av$aid"
  if [ -f $RAW/av$aid.mp4 ]; then
    python ~/dance_win/scripts/data/sheet.py $RAW/av$aid.mp4 $SHEET/av$aid.png --every 1 --max_tiles 48 >/dev/null 2>&1
    echo "[$n] av$aid ok"
  else
    echo "{}" > $RAW/av$aid.skipped   # long video or failure; don't retry
    echo "[$n] av$aid skipped"
  fi
  sleep 1
done
echo "DOWNLOAD_DONE $(ls $RAW/*.mp4 | wc -l) videos"
