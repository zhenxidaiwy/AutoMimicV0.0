#!/usr/bin/env bash
# test_hold.sh <run dir> <ckpt>: eval one checkpoint on the original and on the hold-padded reference, print hold_*
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
D=~/projects/dance/dataset/backflip_3
d=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1
ck=$2
for v in "ballistic labels" "ballistic_hold labels_hold"; do
  set -- $v
  python ~/dance_win/rl/eval_flip.py --ckpt $d/$ck --motion $D/g1_$1_50fps.npz --labels $D/$2_50fps.npz \
    --knee-limit 120 --tag holdtest_$1 2>&1 | grep -E '^\{' | python -c "
import json,sys; r=json.loads(sys.stdin.read()); print('$1', r['clip_s'], {k:v for k,v in r.items() if k.startswith('hold_') or k in ('robot_rotation_deg','stand_stable')})"
done
