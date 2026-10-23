#!/usr/bin/env bash
# Stop any previous search run, then run search_bili.py (resumable) and print the candidate table.
pkill -f search_bili.py 2>/dev/null; sleep 1
P=~/miniforge3/envs/gmr/bin/python
$P ~/dance_win/scripts/data/search_bili.py "${1:-30}"
$P ~/dance_win/scripts/data/show_candidates.py
