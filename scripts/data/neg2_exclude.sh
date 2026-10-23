#!/usr/bin/env bash
# Build the exclusion list of av ids for negative batch 2: batch-1 negatives (raw_neg), raw_unseen, clips.tsv.
# Output: ~/projects/dance/data/search/neg2_exclude.txt (one numeric aid per line)
S=~/projects/dance/data/search; mkdir -p $S
OUT=$S/neg2_exclude.txt
{
  ls ~/projects/dance/data/raw_neg ~/projects/dance/data/raw_unseen 2>/dev/null | grep -oE 'av[0-9]+' | sed 's/^av//'
  grep -oE 'av[0-9]+' ~/projects/dance/live_tests/NEG_README.md | sed 's/^av//'
  grep -oE 'av[0-9]+' ~/dance_win/data/annotations/clips.tsv | sed 's/^av//'
  grep -oE 'BV1[0-9A-Za-z]{9}' ~/dance_win/data/annotations/clips.tsv
} | sort -u > $OUT
echo "exclude: $(wc -l < $OUT) ids"
head -3 ~/dance_win/data/annotations/clips.tsv
ls ~/projects/dance/data/raw_unseen | head -40
