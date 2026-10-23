#!/usr/bin/env bash
# Backflip probe data prep: ballistic variant csv -> npz, then package raw (lock_vlm) + ballistic into dataset/.
# Usage: bash backflip_prep.sh backflip_4 backflip_5 ...
S=~/dance_win/scripts/data; P=~/miniforge3/envs/gmr/bin/python
$P $S/package_backflip.py ballistic "$@" || exit 1
bash $S/to_npz.sh -v ballistic "$@"
$P $S/package_backflip.py package "$@"
