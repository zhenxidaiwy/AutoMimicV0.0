#!/usr/bin/env bash
# Stack groups of overview sheets for review. Usage: bash pos_stack_run.sh <out_name> <aid> [<aid> ...]
SH=~/dance_win/scripts/data/tmp_sheets_pos
O=$1; shift
L=""; for a in "$@"; do L="$L $SH/av$a.png"; done
~/miniforge3/envs/gmr/bin/python -I ~/dance_win/scripts/data/pos_stack.py $SH/stack_$O.png $L
