#!/usr/bin/env bash
# Search Bilibili for standing backflip candidates; metadata for the top-N hits per query (incl. a "## query" header).
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-20}
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/bf_search_bv.txt \
  "原地后空翻" "站立后空翻" "后空翻 教学" "后空翻 一次成功" "立定后空翻" "后空翻 落地" "backflip"
: > $S/bf_search_meta.tsv
cut -f2 $S/bf_search_bv.txt | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/bf_search_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/bf_search_bv.txt | head -n $N | tr '\n' ' ')
  $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $S/bf_search_meta.tsv
done
echo BF_META_DONE $(wc -l < $S/bf_search_meta.tsv)
