#!/usr/bin/env bash
# install the momentum-consistent padded backflip reference as the harness input (dataset/<clip>/g1_ballistic_50fps.npz)
clip=${1:-backflip_3}; DS=~/projects/dance/dataset/$clip; G=~/projects/dance/data/g1/$clip
bash ~/dance_win/scripts/data/to_npz.sh -v ballistic_pad_mc $clip || exit 1
[ -f $DS/g1_ballistic_pad_noMC_50fps.npz ] || cp $DS/g1_ballistic_50fps.npz $DS/g1_ballistic_pad_noMC_50fps.npz
cp $G/g1_ballistic_pad_mc_50fps.npz $DS/g1_ballistic_50fps.npz
~/miniforge3/envs/unitree_rl_mjlab/bin/python -c "
import numpy as np
a = np.load('$DS/g1_ballistic_50fps.npz'); b = np.load('$DS/labels_50fps.npz')
print('npz frames', len(a['joint_pos']), 'labels', len(b['phase']))"
