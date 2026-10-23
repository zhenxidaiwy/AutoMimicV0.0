#!/usr/bin/env bash
# dev check of the exported scene XML (see xml_check.py) in MuJoCo 3.5 and 3.16
source ~/miniforge3/etc/profile.d/conda.sh
cd ~/dance_win/sim2sim || exit 1
conda activate unitree_rl_mjlab; python xml_check.py 2>&1 | tail -n 40
conda activate gmr; python xml_check.py 2>&1 | tail -n 8
