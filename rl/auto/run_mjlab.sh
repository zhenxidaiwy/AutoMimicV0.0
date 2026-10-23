#!/usr/bin/env bash
# Run a command inside the unitree_rl_mjlab conda env with the headless GPU render settings.
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
exec "$@"
