#!/usr/bin/env bash
# annot_prep for several clips with one step size. Usage: bash annot_prep_many.sh <step> <clip> [clip ...]
st=$1; shift
for id in "$@"; do bash ~/dance_win/scripts/data/annot_prep.sh $id $st; done
