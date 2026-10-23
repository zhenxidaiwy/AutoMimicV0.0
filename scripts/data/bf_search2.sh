#!/usr/bin/env bash
# Extra backflip search round (amateur "I finally learned it" uploads tend to use a static phone); metadata, top-N per query.
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-15}
Q=("后空翻 操场" "后空翻 公园" "后空翻 户外" "原地后空翻 展示" "后空翻 草坪" "后空翻 小学生")
$PY -I ~/dance_win/scripts/data/unseen_search.py $S/bf_search_bv.txt "${Q[@]}"
M=$S/bf_search_meta4.tsv; : > $M
for q in "${Q[@]}"; do
  echo "## $q" >> $M
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/bf_search_bv.txt | head -n $N | tr '\n' ' ')
  [ -n "$BVS" ] && $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $M
done
# compact listing: only <=90 s videos
awk -F'\t' '/^##/ {print; next} $3+0>0 && $3+0<=90 {print $2"\t"$3"\t"substr($8,1,40)}' $M
