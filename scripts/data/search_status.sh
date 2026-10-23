#!/usr/bin/env bash
# Show search progress: process age, rows so far, last row.
ps -eo pid,etime,args | grep -E "search_bili|yt_dlp" | grep -v grep | cut -c1-140
F=~/projects/dance/data/search/candidates_meta.jsonl
echo "rows: $(wc -l < $F)"; tail -n 1 $F | cut -c1-300
