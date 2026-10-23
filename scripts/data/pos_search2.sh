#!/usr/bin/env bash
# Second positive-training search round: more specific queries + deeper pages of the base queries.
# Metadata only for ids not seen in any earlier search metadata. Output: pos_search2_bv.txt, pos_search2_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
D=~/dance_win/scripts/data
S=~/projects/dance/data/search; N=${1:-25}
B=$S/pos_search2_bv.txt
cp $S/pos_search_bv.txt $B.seed 2>/dev/null
PAGES=1-2 $PY $D/pos_search_pages.py $B \
  "狗熊哆嗦毛 交作业" "狗熊哆嗦毛 还原" "狗熊哆嗦毛 复刻" "狗熊哆嗦毛 原速" "狗熊哆嗦毛 完整" "鼓子秧歌 翻跳" \
  "明文军 狗熊哆嗦毛 翻跳" "狗熊哆嗦毛 我也来" "狗熊哆嗦毛 舞蹈生" "狗熊哆嗦毛 老师" \
  "闪身步 原速" "闪身步 正面" "闪身步 交作业" "闪身步 还原" "闪身步 我也来" "闪身步 舞蹈生" "闪身步 赵铁春 翻跳"
PAGES=3-5 $PY $D/pos_search_pages.py $B "狗熊哆嗦毛" "闪身步"
OLD=$S/pos_old_bv.txt
cat $S/*.tsv 2>/dev/null | grep -oE 'BV1[0-9A-Za-z]{9}' | sort -u > $OLD
: > $S/pos_search2_meta.tsv
cut -f2 $B | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/pos_search2_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $B | grep -vxFf $OLD | head -n $N | tr '\n' ' ')
  [ -n "$BVS" ] && $PY -I $D/unseen_fetch.py meta $BVS >> $S/pos_search2_meta.tsv
done
echo POS2_META_DONE $(wc -l < $S/pos_search2_meta.tsv)
