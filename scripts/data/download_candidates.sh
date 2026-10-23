#!/usr/bin/env bash
# download_candidates.sh <list.tsv>: download every '<motion>\t<url>' into ~/projects/dance/raw/candidates_2026-10-23/<motion>/
# (personal research only; never published). Resumable via the yt-dlp download archive; failures logged.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
OUT=~/projects/dance/raw/candidates_2026-10-23
mkdir -p $OUT
while IFS=$'\t' read -r motion url; do
  [ -z "$url" ] && continue
  mkdir -p "$OUT/$motion"
  echo "== $motion $url"
  yt-dlp -q --no-warnings --download-archive "$OUT/archive.txt" -f "bv*[height<=1080]+ba/b[height<=1080]/b" \
    --merge-output-format mp4 --sleep-requests 1 --retries 3 --write-info-json \
    -o "$OUT/$motion/%(id)s_%(title).60B.%(ext)s" "$url" || echo "FAILED $motion $url" | tee -a "$OUT/failed.txt"
  sleep 2
done < "$1"
echo "done: $(find $OUT -name '*.mp4' | wc -l) mp4 files"; cat "$OUT/failed.txt" 2>/dev/null
du -sh $OUT
