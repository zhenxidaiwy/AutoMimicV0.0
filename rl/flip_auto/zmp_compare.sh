#!/usr/bin/env bash
# zmp_compare.sh [cartwheel npz ...]: ref_zmp.py summaries of cartwheel_2 reference variants vs the backflip_3 one
# (which trained fine)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
D=~/projects/dance/dataset
for v in ${@:-g1_plant_vlm_hold_50fps.npz}; do
  echo "CARTWHEEL $v"; python ref_zmp.py $D/cartwheel_2/$v --labels $D/cartwheel_2/labels_hold_50fps.npz --quiet | tail -n +3
done
echo BACKFLIP; python ref_zmp.py $D/backflip_3/g1_ballistic_hold_50fps.npz --labels $D/backflip_3/labels_hold_50fps.npz --quiet | tail -n +3
