#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*bda_zhao_sss_lock_vlm_adaptive_n4096 | tail -1)
python ~/dance_win/rl/eval_ckpt.py --ckpt $dir/model_0.pt --motion ~/projects/dance/dataset/bda_zhao_sss/g1_lock_vlm_50fps.npz --debug 2>&1 | grep -E "debug|Error|Traceback|line"
