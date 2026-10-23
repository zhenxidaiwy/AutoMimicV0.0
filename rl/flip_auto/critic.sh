#!/usr/bin/env bash
# critic.sh <run dir name> <ckpt>: HD evaluation (with full record) + automatic critic report + worst-frame sheet
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
dir=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1
bash ~/dance_win/rl/flip_auto/peek_hd.sh $1 $2 > /dev/null
python ~/dance_win/rl/flip_auto/critic.py $dir/eval/flip_hd_${2%.pt}_record.npz \
  ~/projects/dance/dataset/backflip_3/labels_50fps.npz $dir/eval/flip_hd_${2%.pt}.mp4
cp $dir/eval/flip_hd_${2%.pt}_critic.md $dir/eval/flip_hd_${2%.pt}_critic_worst.jpg ~/dance_win/videos/backflip/auto/ 2>/dev/null
