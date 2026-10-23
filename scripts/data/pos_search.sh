#!/usr/bin/env bash
# Search Bilibili for POSITIVE-training candidates (new performers of 狗熊哆嗦毛 / 闪身步), then metadata for the
# top-N new hits per query (with a "## query" header per block). Skips ids already in older search metadata.
# Output: ~/projects/dance/data/search/pos_search_bv.txt, pos_search_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-20}
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/pos_search_bv.txt \
  "狗熊哆嗦毛 女生" "狗熊哆嗦毛 男生" "狗熊哆嗦毛 学会了" "狗熊哆嗦毛 一镜到底" "狗熊哆嗦毛 全身" \
  "狗熊哆嗦毛 跟跳" "狗熊哆嗦毛 宿舍" "狗熊哆嗦毛 练习室" "狗熊哆嗦毛 小孩" "哆嗦毛 翻跳" "狗熊哆嗦毛 模仿" \
  "闪身步 翻跳" "闪身步 挑战" "闪身步 跟跳" "闪身步 一镜到底" "闪身步 全身" "闪身步 练习室" \
  "闪身步 女生" "闪身步 男生" "闪身步 宿舍" "闪身步 学会了"
OLD=$S/pos_old_bv.txt
cat $S/unseen_search_meta.tsv $S/unseen_meta.tsv $S/*.tsv 2>/dev/null | grep -oE 'BV1[0-9A-Za-z]{9}|av[0-9]+' | sort -u > $OLD
: > $S/pos_search_meta.tsv
cut -f2 $S/pos_search_bv.txt | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/pos_search_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/pos_search_bv.txt | grep -vxFf $OLD | head -n $N | tr '\n' ' ')
  $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $S/pos_search_meta.tsv
done
echo POS_META_DONE $(wc -l < $S/pos_search_meta.tsv)
