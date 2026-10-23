#!/usr/bin/env bash
# Fetch title/duration/uploader for every search candidate via the mobile page (no download), for held-out test selection.
# Output: ~/projects/dance/data/search/unseen_meta.tsv
PY=~/miniforge3/envs/gmr/bin/python
OUT=~/projects/dance/data/search/unseen_meta.tsv
EXCL="117285977068813 117312921404527 117332315867932 117346945600980 117416621246346 117438683289595 117381925963568"
# 狗熊哆嗦毛 ids first
IDS=$($PY -I -c "import json,os; d=json.load(open(os.path.expanduser('~/projects/dance/data/search/ids.json'))); g=[a for a,q in d.items() if any('狗熊' in x for x in q)]; print(' '.join(g+[a for a in d if a not in g]))")
LIST=""
for aid in $IDS; do
  case " $EXCL " in *" $aid "*) continue;; esac
  LIST="$LIST $aid"
done
$PY -I ~/dance_win/scripts/data/unseen_fetch.py meta $LIST > $OUT
echo META_DONE $(wc -l < $OUT)
