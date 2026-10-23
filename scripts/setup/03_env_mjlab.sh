#!/usr/bin/env bash
# RL env: unitree_rl_mjlab (mjlab 1.2.0 + mujoco-warp 3.5.0, Isaac-Lab-style API on MuJoCo Warp).
set -e
source ~/miniforge3/etc/profile.d/conda.sh
conda env list | grep -q "^unitree_rl_mjlab " || conda create -y -q -n unitree_rl_mjlab python=3.11
conda activate unitree_rl_mjlab
cd ~/projects/unitree_rl_mjlab
pip install -q -e .
python - <<'EOF'
import torch, mujoco, warp, mjlab
print("torch", torch.__version__, "cuda", torch.version.cuda, "ok", torch.cuda.is_available(),
      "cap", torch.cuda.get_device_capability(0), "arch_list", torch.cuda.get_arch_list())
print("mujoco", mujoco.__version__, "warp", warp.__version__)
EOF
pip list 2>/dev/null | grep -iE "^(mjlab|mujoco|mujoco-warp|warp-lang|rsl-rl-lib|torch|onnx) "
echo DONE_MJLAB
