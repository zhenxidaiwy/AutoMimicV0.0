#!/usr/bin/env bash
# Search Bilibili (server-rendered search pages) for NEGATIVE test candidates (non-target motions),
# then fetch metadata via the mobile page. Output: ~/projects/dance/data/search/neg_search_bv.txt, neg_search_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/neg_search_bv.txt \
  "原地踏步 全身" "走路 全身 正面" "开合跳" "开合跳 跟练" "深蹲 教学" "侧弓步" "侧弓步 教学" "热身运动 跟练" \
  "科目三 单人" "科目三 舞蹈" "广场舞 单人 正面" "花鼓灯 教学" "原地跳绳" "站着讲解 全身"
BVS=$(cut -f1 $S/neg_search_bv.txt | tr '\n' ' ')
$PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS > $S/neg_search_meta.tsv
echo NEG_META_DONE $(wc -l < $S/neg_search_meta.tsv)
