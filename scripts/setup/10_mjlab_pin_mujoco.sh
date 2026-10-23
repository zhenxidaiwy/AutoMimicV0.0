#!/usr/bin/env bash
# mujoco-warp 3.5.0 (pinned by unitree_rl_mjlab) needs the matching mujoco 3.5.0; pip had pulled 3.16.0.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
# warp-lang 1.18 removed wp.context which mujoco-warp 3.5.0 uses; mjlab 1.2.0 needs >=1.12 -> pin 1.12.x
pip install -q "mujoco==3.5.0" "warp-lang>=1.12,<1.13" scipy   # scipy: imported by mjlab.terrains but not declared
python -c "import warp; print('warp', warp.__version__)"
pip check 2>&1 | grep -iE "mujoco|mjlab|warp" || echo "pip check: no mujoco/mjlab/warp conflicts"
python -c "
import mujoco, mujoco_warp, mjlab
print('mujoco', mujoco.__version__, '| mujoco_warp import ok')"
