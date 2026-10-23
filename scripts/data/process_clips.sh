#!/usr/bin/env bash
# Run clip_and_gvhmr.sh for every row of data/annotations/clips.tsv whose G1 output is missing.
# Usage: bash process_clips.sh [clip_id ...]   (no args = all pending)
TSV=~/dance_win/data/annotations/clips.tsv
L=~/projects/dance_logs; mkdir -p $L
grep -v "^#" $TSV | while IFS=$'\t' read -r raw cid ss to cam move perf note; do
  [ -z "$cid" ] && continue
  if [ $# -gt 0 ] && [[ ! " $* " =~ " $cid " ]]; then continue; fi
  [ -f ~/projects/dance/data/g1/$cid/g1.csv ] && { echo "skip $cid (done)"; continue; }
  echo "=== $cid $(date +%T)"
  bash ~/dance_win/scripts/data/clip_and_gvhmr.sh $raw $cid $ss $to $cam > $L/clip_$cid.log 2>&1 < /dev/null \
    && grep -E "^\{" $L/clip_$cid.log || { echo "FAILED $cid"; tail -5 $L/clip_$cid.log; }
done
echo ALL_DONE
