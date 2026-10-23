#!/usr/bin/env bash
# G1 csv (30 fps) -> mjlab tracking npz (50 fps, all body poses/velocities via MuJoCo FK).
# Usage: bash to_npz.sh [-v variant] <clip_id> [clip_id ...]
#   no variant : data/g1/<id>/g1.csv              -> g1_50fps.npz
#   -v ground_vlm : data/g1/<id>/g1_ground_vlm.csv -> g1_ground_vlm_50fps.npz
var=""
if [ "$1" = "-v" ]; then var=$2; shift 2; fi
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/projects/unitree_rl_mjlab
for id in "$@"; do
  G=~/projects/dance/data/g1/$id
  if [ -z "$var" ]; then in=$G/g1.csv; name=$id; out=$G/g1_50fps.npz
  else in=$G/g1_$var.csv; name=${id}__$var; out=$G/g1_${var}_50fps.npz; fi
  python scripts/csv_to_npz.py --robot g1 --input-file $in --output-name $name --input-fps 30 --output-fps 50 \
    > ~/projects/dance_logs/npz_$name.log 2>&1
  if [ -f src/assets/motions/g1/$name.npz ]; then
    cp src/assets/motions/g1/$name.npz $out && echo "npz ok $name"
  else
    echo "npz FAILED $name"; tail -5 ~/projects/dance_logs/npz_$name.log
  fi
done
