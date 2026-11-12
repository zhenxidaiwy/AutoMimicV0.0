#!/usr/bin/env bash
# find_motion_cmd.sh: where mjlab's tracking MotionCommand keeps the reference body positions
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
d=$(python -c "import mjlab, os; print(os.path.dirname(mjlab.__file__))")
f=$(grep -rl "class MotionCommand" "$d" | head -1)
echo "$f"
grep -n "body_pos_w\|class MotionLoader\|body_indexes\|self.motion = \|time_steps\|def body_pos_relative_w" "$f" | head -40
