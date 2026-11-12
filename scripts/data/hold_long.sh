#!/usr/bin/env bash
# hold_long.sh <clip> <variant> [rest_s]: reference with a LONG held final pose (default 7.5 s = the 2 s judged hold +
# the 5 s evaluated past the reference + settling), so training covers the whole window the evaluation judges
# -> dataset/<clip>/g1_<variant>_hold8_50fps.npz + labels_hold8_50fps.npz
id=$1; var=$2; R=${3:-7.5}
P=~/miniforge3/envs/gmr/bin/python; S=~/dance_win/scripts/data; D=~/projects/dance/dataset/$id
$P $S/hold_tail.py $D/g1_${var}_50fps.npz $D/labels_50fps.npz $D/g1_${var}_hold8_50fps.npz $D/labels_hold8_50fps.npz --rest_s $R
$P $S/inspect_ref.py $D/g1_${var}_hold8_50fps.npz $D/labels_hold8_50fps.npz
