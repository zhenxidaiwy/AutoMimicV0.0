#!/usr/bin/env bash
# find_episode_len.sh: episode length setting of the mjlab tracking task (does a longer reference fit one episode?)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
d=$(python -c "import mjlab, os; print(os.path.dirname(mjlab.__file__))")
grep -rn "episode_length_s" "$d/tasks/tracking" ~/projects/unitree_rl_mjlab/src 2>/dev/null | head
grep -n "time_out\|time_step_total" "$d/tasks/tracking/mdp/commands.py" | head
