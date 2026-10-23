#!/usr/bin/env bash
# sim_dt.sh: physics timestep and decimation of the tracking task (for the action-delay unit)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/projects/unitree_rl_mjlab && python - <<'EOF'
import mjlab.tasks, src.tasks  # noqa
from mjlab.tasks.registry import load_env_cfg
c = load_env_cfg("Unitree-G1-Tracking-No-State-Estimation")
print("timestep", c.sim.mujoco.timestep, "decimation", c.decimation)
print([type(a).__name__ for a in c.scene.entities["robot"].articulation.actuators])
EOF
