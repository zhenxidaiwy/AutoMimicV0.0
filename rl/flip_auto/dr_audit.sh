#!/usr/bin/env bash
# dr_audit.sh: which domain randomisation / disturbance events the tracking task trains with
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
P=$(python -c "import mjlab, os; print(os.path.dirname(mjlab.__file__))")
echo "mjlab at $P"
grep -rn -E "EventTermCfg\(|push|friction|mass|com_|kp|kd|latency|delay|noise" $P/tasks/tracking/*.py $P/tasks/tracking/config/g1/*.py 2>/dev/null | grep -v "^.*#" | cut -c 1-220 | head -60
grep -n -E "events|push|friction|noise|randomi" ~/dance_win/rl/train_dance.py | cut -c 1-200 | head -30
