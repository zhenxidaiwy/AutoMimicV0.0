#!/usr/bin/env bash
# Search Bilibili for NEGATIVE test candidates, batch 2 (held-out categories), then metadata for the top-N
# hits per query (with a "## query" header per block). Reuses unseen_search.py / unseen_fetch.py.
# Output: ~/projects/dance/data/search/neg2_search_bv.txt, neg2_search_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-14}
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/neg2_search_bv.txt \
  "kpop翻跳 单人 全身" "韩舞翻跳 镜面 一镜到底" "街舞 freestyle 单人" "breaking 单人 练习室" \
  "健身操 跟练 全身" "有氧操 跟练" "太极拳 24式 正面" "八段锦 完整版 正面" \
  "空击 拳击 训练" "拳击 步法 练习" "瑜伽流 跟练 全身" "拜日式 跟练" \
  "原地跳绳 无绳" "原地慢跑 跟练" "拉丁舞 恰恰 基本步" "爵士舞 单人 练习室" \
  "站着打招呼 挥手" "手势舞 单人 全身" "走路 转身 全身" "模特 走秀 练习" \
  "海草舞 单人" "极乐净土 单人 全身" "魔性舞蹈 单人 全身" "鬼步舞 单人"
: > $S/neg2_search_meta.tsv
cut -f2 $S/neg2_search_bv.txt | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/neg2_search_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/neg2_search_bv.txt | head -n $N | tr '\n' ' ')
  $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $S/neg2_search_meta.tsv
done
echo NEG2_META_DONE $(wc -l < $S/neg2_search_meta.tsv)
