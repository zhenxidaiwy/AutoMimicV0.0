#!/usr/bin/env bash
# bili_retry.sh: wait until Bilibili's IP risk control (HTTP 412) lifts - one probe every 15 min, max 12 h - then
# download the failed Bilibili candidates slowly (20 s apart) with bili_dl.py. Personal research only.
OUT=~/projects/dance/raw/candidates_2026-10-23
LIST=~/dance_win/data/video_candidates_2026-10-23.tsv
for i in $(seq 1 48); do
  if python3 ~/dance_win/scripts/data/bili_dl.py BV1ys411N771 x --probe >/dev/null 2>&1; then echo "API open after $i probes"; break; fi
  [ "$i" = 48 ] && { echo "still blocked after 12 h"; exit 1; }
  sleep 900
done
grep bilibili "$LIST" | while IFS=$'\t' read -r motion url; do
  bv=$(echo "$url" | grep -oE 'BV[0-9A-Za-z]+')
  ls "$OUT/$motion/${bv}"*.mp4 >/dev/null 2>&1 && continue
  mkdir -p "$OUT/$motion"
  python3 ~/dance_win/scripts/data/bili_dl.py "$bv" "$OUT/$motion/$bv.mp4" 2>&1 | tail -1 || echo "FAILED $bv"
  sleep 20
done
bash ~/dance_win/scripts/data/candidates_status.sh
