#!/usr/bin/env bash
# pad_landing.sh <clip> <variant>: stand-up tail -> npz -> labels; then install as the harness inputs
# (dataset/<clip>/g1_<variant>_50fps.npz and labels_50fps.npz; originals kept as *_nopad*).
S=~/dance_win/scripts/data; P=~/miniforge3/envs/gmr/bin/python
clip=$1; var=$2; G=~/projects/dance/data/g1/$clip; DS=~/projects/dance/dataset/$clip
$P $S/pad_landing.py $clip $var || exit 1
bash $S/to_npz.sh -v ${var}_pad $clip || exit 1
cp $G/g1_${var}_pad_50fps.npz $DS/ || exit 1
$P $S/pad_landing.py $clip ${var} --labels || exit 1
[ -f $DS/g1_${var}_nopad_50fps.npz ] || cp $DS/g1_${var}_50fps.npz $DS/g1_${var}_nopad_50fps.npz
[ -f $DS/labels_nopad_50fps.npz ] || cp $DS/labels_50fps.npz $DS/labels_nopad_50fps.npz
cp $DS/g1_${var}_pad_50fps.npz $DS/g1_${var}_50fps.npz
cp $DS/labels_pad_50fps.npz $DS/labels_50fps.npz
ls -la $DS
