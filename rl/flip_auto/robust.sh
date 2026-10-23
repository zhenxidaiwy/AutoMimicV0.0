#!/usr/bin/env bash
# robust.sh <run dir name> <ckpt> [scenarios] [envs]: robustness evaluation of a harness checkpoint
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
d=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1
mkdir -p $d/eval
python ~/dance_win/rl/eval_flip_robust.py --ckpt $d/$2 --motion ~/projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz \
  --knee-limit 120 --scenarios ${3:-nominal,dr,delay1,delay2,kp085} --envs ${4:-256} --out $d/eval/robust_${2%.pt}.json 2>&1 \
  | grep -E '^\{|Error|Traceback|error' | cut -c 1-400
