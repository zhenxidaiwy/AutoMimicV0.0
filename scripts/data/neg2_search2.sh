#!/usr/bin/env bash
# Second search round for negative batch 2 (gap categories: aerobics, waving/gesturing, boxing, hip-hop, meme dance).
# Output: ~/projects/dance/data/search/neg2_search2_bv.txt, neg2_search2_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-12}
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/neg2_search2_bv.txt \
  "动作参考 挥手" "动作参考 打招呼" "动作参考 出拳" "动作参考 走路" "动作参考 跳舞" \
  "健身操 单人 正面 全身" "有氧操 镜面 单人" "健美操 单人 成套" "燃脂操 单人 正面" \
  "影子拳 单人" "hiphop freestyle 练习室 一镜到底" "popping freestyle 单人" \
  "子弹舞 单人" "挖呀挖 舞蹈 单人" "picopico 舞蹈 单人"
: > $S/neg2_search2_meta.tsv
cut -f2 $S/neg2_search2_bv.txt | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/neg2_search2_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/neg2_search2_bv.txt | head -n $N | tr '\n' ' ')
  $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $S/neg2_search2_meta.tsv
done
echo NEG2_META2_DONE $(wc -l < $S/neg2_search2_meta.tsv)
