#!/usr/bin/env bash
# Replay a packaged 闪身步 policy in simulation and write a video (no training needed).
# Usage (in Ubuntu): bash ~/dance_win/policies/replay.sh [policy_dir=sss_bda_v1]
# Output: <policy_dir>/eval/policy.mp4 + policy.json (completed? tracking error)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
P=~/dance_win/policies/${1:-sss_bda_v1}
python ~/dance_win/rl/eval_ckpt.py --ckpt $P/policy.pt --motion $P/reference_motion.npz 2>&1 | grep -E '^\{|Error|Traceback'
echo "video: $P/eval/policy.mp4"
