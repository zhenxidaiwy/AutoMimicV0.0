#!/usr/bin/env bash
# Positive-training batch: exclusion list of av ids (raw_unseen, raw_neg, raw_neg2, clips.tsv, live_tests READMEs)
# + contact sheets of the held-out unseen test clips (to check performers visually).
# Output: ~/projects/dance/data/search/pos_exclude.txt
S=~/projects/dance/data/search; mkdir -p $S
OUT=$S/pos_exclude.txt
L=~/projects/dance/live_tests
{
  ls ~/projects/dance/data/raw_neg ~/projects/dance/data/raw_unseen ~/projects/dance/data/raw_neg2 2>/dev/null | grep -oE 'av[0-9]+' | sed 's/^av//'
  grep -ohE 'av[0-9]+' $L/UNSEEN_README.md $L/NEG_README.md $L/NEG2_README.md | sed 's/^av//'
  grep -oE 'av[0-9]+' ~/dance_win/data/annotations/clips.tsv | sed 's/^av//'
  grep -ohE 'BV1[0-9A-Za-z]{9}' ~/dance_win/data/annotations/clips.tsv $L/UNSEEN_README.md $L/NEG_README.md $L/NEG2_README.md
} | sort -u > $OUT
echo "exclude: $(wc -l < $OUT) ids"
head -2 ~/dance_win/data/annotations/clips.tsv
cut -f1-3 ~/dance_win/data/annotations/clips.tsv | head -60
SH=~/dance_win/scripts/data/tmp_sheets_pos; mkdir -p $SH
for f in unseen_sss_1 unseen_sss_2 unseen_sss_3 unseen_gxdsm_1 unseen_gxdsm_2 unseen_gxdsm_3; do
  ~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/sheet.py $L/$f.mp4 $SH/test_$f.png --every 0.5 --cols 8 --w 120 --max_tiles 24
done
