#!/usr/bin/env bash
# Start the live server (or a benchmark). Usage: bash server.sh [extra args, e.g. --bench gym_sss]
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*multi_canon_v1* | tail -1)
ck=$(ls $dir/model_*.pt | sort -V | tail -1)
# per-dance specialist trackers (the single-clip policies the user liked; 闪身步 step amplitude 72% of the reference
# in live follow vs 57% with the multi-clip canon_v1); canon_v1 stays loaded as the default tracker
SP="0=$HOME/dance_win/policies/sss_bda_v1/policy.pt,1=$HOME/dance_win/policies/gxdsm_full_v1/policy.pt"
python ~/dance_win/live/server.py --ckpt $ck --watch ret_lead0_s0 --dance_ckpts "$SP" "$@" 2>&1 | \
  grep --line-buffered -vE "Warning|warn|Module .* load on device"
