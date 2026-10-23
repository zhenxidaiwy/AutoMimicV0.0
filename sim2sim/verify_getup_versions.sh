#!/usr/bin/env bash
source ~/miniforge3/etc/profile.d/conda.sh
conda activate gmr
python -c "import mujoco; print('gmr mujoco', mujoco.__version__)"
conda activate unitree_rl_mjlab
python -c "import mujoco, mujoco_warp; print('unitree_rl_mjlab mujoco', mujoco.__version__, 'warp', getattr(mujoco_warp, '__version__', '?'))"
pgrep -af "native_getup|native_dance" || echo "no native_* processes running"
