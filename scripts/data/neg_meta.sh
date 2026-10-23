#!/usr/bin/env bash
# Metadata for the top-N search hits per query (neg_search_bv.txt keeps per-query result order).
# Output: ~/projects/dance/data/search/neg_search_meta.tsv (one "## query" header per block)
pkill -f "unseen_fetch.py meta" 2>/dev/null   # stop my earlier full-list meta run
pkill -f neg_search.sh 2>/dev/null
PY=~/miniforge3/envs/gmr/bin/python
S=~/projects/dance/data/search; N=${1:-20}
: > $S/neg_search_meta.tsv
cut -f2 $S/neg_search_bv.txt | awk '!seen[$0]++' | while IFS= read -r q; do
  echo "## $q" >> $S/neg_search_meta.tsv
  BVS=$(awk -F'\t' -v q="$q" '$2==q {print $1}' $S/neg_search_bv.txt | head -n $N | tr '\n' ' ')
  $PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $BVS >> $S/neg_search_meta.tsv
done
echo NEG_META_DONE $(wc -l < $S/neg_search_meta.tsv)
