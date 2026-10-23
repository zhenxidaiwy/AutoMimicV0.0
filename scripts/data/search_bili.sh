#!/usr/bin/env bash
# List Bilibili search results (metadata only, no download) for candidate dance clips.
# Usage: bash search_bili.sh [N per query]  -> ~/projects/dance/data/search/candidates.jsonl
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
N=${1:-30}
OUT=~/projects/dance/data/search; mkdir -p $OUT; : > $OUT/candidates.jsonl
while read -r q; do
  [ -z "$q" ] && continue
  echo "## $q"
  yt-dlp --flat-playlist -j --sleep-requests 1 "bilisearch$N:$q" 2>>$OUT/errors.log \
    | python -c '
import sys, json
q = sys.argv[1]
for line in sys.stdin:
    d = json.loads(line)
    out = {k: d.get(k) for k in ("id", "title", "duration", "uploader", "view_count", "url")}
    out["query"] = q
    print(json.dumps(out, ensure_ascii=False))
' "$q" | tee -a $OUT/candidates.jsonl | wc -l
done <<'EOF'
闪身步
闪身步 教学
闪身步 花鼓灯
花鼓灯 闪身步 赵铁春
闪身步 翻跳
闪身步 挑战
狗熊哆嗦毛
EOF
python - <<'EOF'
import json, os
p = os.path.expanduser("~/projects/dance/data/search/candidates.jsonl")
rows = {}
for l in open(p):
    d = json.loads(l); rows.setdefault(d["id"], d)
print("unique candidates:", len(rows))
EOF
