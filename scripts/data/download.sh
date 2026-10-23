#!/usr/bin/env bash
# Download Bilibili videos (video stream only, <=720p) and make a 1 s contact sheet for each.
# Usage: bash download.sh BVxxxx [BVyyyy ...]
# Raw videos stay in ~/projects/dance/data/raw (personal research use only, never published).
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
RAW=~/projects/dance/data/raw; SHEET=~/dance_win/data/qa/sheets; mkdir -p $RAW $SHEET
for bv in "$@"; do
  if [ ! -f $RAW/$bv.mp4 ]; then
    python -m yt_dlp -q --no-warnings --sleep-requests 1 -f "bv*[height<=720][vcodec^=avc]/bv*[height<=720]/bv*" \
      --remux-video mp4 -o "$RAW/$bv.%(ext)s" "https://www.bilibili.com/video/$bv" || { echo "FAIL $bv"; continue; }
  fi
  python ~/dance_win/scripts/data/sheet.py $RAW/$bv.mp4 $SHEET/$bv.png --every 1
  sleep 2
done
