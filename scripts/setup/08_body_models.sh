#!/usr/bin/env bash
# Install SMPL-X / SMPL body models (license-gated, downloaded by the user) into GVHMR and GMR.
# Usage: bash 08_body_models.sh [dir with models_smplx_v1_1.zip and SMPL_python_v.1.1.0.zip]
set -e
SRC=${1:-/mnt/c/Users/user/Downloads}
DST=~/projects/dance/body_models          # one copy on ext4, symlinked into both repos
TMP=$(mktemp -d)
mkdir -p $DST/smplx $DST/smpl

unzip -oq "$SRC/models_smplx_v1_1.zip" -d $TMP/smplx
unzip -oq "$SRC/SMPL_python_v.1.1.0.zip" -d $TMP/smpl
for g in NEUTRAL MALE FEMALE; do cp "$(find $TMP/smplx -name "SMPLX_$g.npz" | head -1)" $DST/smplx/; done
cp "$(find $TMP/smpl -name 'basicmodel_neutral_lbs_10_207_0_v1.1.0.pkl' | head -1)" $DST/smpl/SMPL_NEUTRAL.pkl
rm -rf $TMP

# GVHMR expects inputs/checkpoints/body_models/{smplx/SMPLX_*.npz, smpl/SMPL_NEUTRAL.pkl}
G=~/projects/GVHMR/inputs/checkpoints/body_models; mkdir -p $G/smplx $G/smpl
ln -sf $DST/smplx/*.npz $G/smplx/; ln -sf $DST/smpl/SMPL_NEUTRAL.pkl $G/smpl/
# GMR expects assets/body_models/smplx/SMPLX_*.npz (smplx.create default ext is npz)
M=~/projects/GMR/assets/body_models/smplx; mkdir -p $M; ln -sf $DST/smplx/*.npz $M/
ls -la $DST/smplx $DST/smpl

source ~/miniforge3/etc/profile.d/conda.sh
conda activate gmr
python -c "
import smplx, torch
m = smplx.create('$HOME/projects/GMR/assets/body_models', 'smplx', gender='neutral', use_pca=False)
print('GMR  smplx neutral ok, joints:', m().joints.shape)"
conda activate gvhmr
cd ~/projects/GVHMR
python -c "
from hmr4d.utils.smplx_utils import make_smplx
print('GVHMR supermotion ok:', type(make_smplx('supermotion')).__name__)
print('GVHMR smpl ok, faces:', make_smplx('smpl').faces.shape)"
echo DONE_BODY_MODELS
