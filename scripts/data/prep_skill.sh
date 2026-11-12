#!/usr/bin/env bash
# prep_skill.sh <clip> <variant>: csv variant -> 50 fps npz -> dataset package -> held final pose (2.5 s)
# -> dataset/<clip>/g1_<variant>_hold_50fps.npz + labels_hold_50fps.npz
id=$1; var=$2
S=~/dance_win/scripts/data; P=~/miniforge3/envs/gmr/bin/python
bash $S/to_npz.sh -v $var $id || exit 1
$P $S/package_skill.py $id $var || exit 1
D=~/projects/dance/dataset/$id
$P $S/hold_tail.py $D/g1_${var}_50fps.npz $D/labels_50fps.npz $D/g1_${var}_hold_50fps.npz $D/labels_hold_50fps.npz
$P $S/inspect_ref.py $D/g1_${var}_hold_50fps.npz $D/labels_hold_50fps.npz
