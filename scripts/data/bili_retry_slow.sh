#!/usr/bin/env bash
# bili_retry_slow.sh: download the remaining Bilibili candidates very slowly (Bilibili IP risk control, HTTP 412):
# 3 min between videos, 20 min pause after a 412, give up after 16 h. Personal research only.
OUT=~/projects/dance/raw/candidates_2026-10-23
LIST=~/dance_win/data/video_candidates_2026-10-23.tsv
rmdir "$OUT/eezes_toprock" 2>/dev/null
end=$(( $(date +%s) + 16 * 3600 ))
while [ "$(date +%s)" -lt "$end" ]; do
  left=0
  while IFS=$'\t' read -r motion url <&3; do
    [ -z "$url" ] && continue
    bv=$(echo "$url" | grep -oE 'BV[0-9A-Za-z]+')
    [ -z "$bv" ] && continue
    ls "$OUT/$motion/${bv}"*.mp4 >/dev/null 2>&1 && continue
    left=$((left + 1))
    mkdir -p "$OUT/$motion"
    if python3 ~/dance_win/scripts/data/bili_dl.py "$bv" "$OUT/$motion/$bv.mp4" >/tmp/bili_last.log 2>&1; then
      echo "$(date +%H:%M) ok $motion $bv"; sleep 180
    else
      grep -q 412 /tmp/bili_last.log && { echo "$(date +%H:%M) 412 -> pause 20 min"; sleep 1200; } || { echo "$(date +%H:%M) failed $bv: $(tail -1 /tmp/bili_last.log)"; sleep 60; }
    fi
    [ "$(date +%s)" -ge "$end" ] && break
  done 3< "$LIST"
  [ "$left" = 0 ] && break
done
bash ~/dance_win/scripts/data/candidates_status.sh
