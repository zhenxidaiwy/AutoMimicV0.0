#!/usr/bin/env bash
# Several fine sheets at once. Args: triples "<raw_id> <start> <end>" ...; every 0.25 s, narrow tiles (portrait video).
while [ $# -ge 3 ]; do
  bash ~/dance_win/scripts/data/fine_sheet.sh $1 $2 $3 0.25 130
  shift 3
done
