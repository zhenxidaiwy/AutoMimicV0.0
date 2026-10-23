#!/usr/bin/env bash
# Retargeting env: GMR (SMPL-X -> Unitree G1 29-DoF via mink IK). Also hosts yt-dlp for video download.
set -e
source ~/miniforge3/etc/profile.d/conda.sh
conda env list | grep -q "^gmr " || conda create -y -q -n gmr python=3.10
conda activate gmr
cd ~/projects/GMR
pip install -q -e . yt-dlp
conda install -y -q -c conda-forge libstdcxx-ng   # GMR README: fixes mujoco rendering libstdc++ errors
python -c "import general_motion_retargeting, mujoco, mink, smplx, torch; print('gmr ok | mujoco', mujoco.__version__, '| torch', torch.__version__)"
yt-dlp --version
echo DONE_GMR
