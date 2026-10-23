#!/usr/bin/env bash
# Search more held-out candidates (狗熊哆嗦毛 first), then fetch metadata for the new BV ids.
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/unseen_search_bv.txt \
  "狗熊哆嗦毛" "狗熊哆嗦毛 翻跳" "狗熊哆嗦毛 教学" "狗熊哆嗦毛 挑战" "狗熊哆嗦毛 舞蹈" "狗熊哆嗦毛 跳"
BVS=$(cut -f1 $S/unseen_search_bv.txt | tr '\n' ' ')
$PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS > $S/unseen_search_meta.tsv
echo SEARCH_META_DONE $(wc -l < $S/unseen_search_meta.tsv)
