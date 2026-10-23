#!/usr/bin/env bash
# Backflip probe, per clip after GVHMR + retarget: re-time the flip -> events -> postprocess -> ballistic variant ->
# dataset package. Usage: bash backflip_full.sh 2 3 7 8
S=~/dance_win/scripts/data; P=~/miniforge3/envs/gmr/bin/python
$P $S/retime_flip.py "$@" || exit 1
$P $S/make_backflip_events.py "$@" || exit 1
ids=$(for k in "$@"; do printf "backflip_%s " $k; done)
bash $S/postprocess.sh $ids 2>&1 | grep -E "^backflip|npz|\"contacts\": \"vlm\"" | cut -c 1-260
bash $S/backflip_prep.sh $ids
