#!/usr/bin/env bash
# launch_task.sh <task> K: run exactly round K of <task> in LLM mode (needs <task root>/decisions/rKK.json), then exit
# so the agent is notified. Tasks: rl/flip_auto/taskcfg.py (backflip_3 = the historical paths).
export AUTOMIMIC_TASK=$1; K=$2
cd ~/dance_win/rl/flip_auto || exit 1
f=$(python3 -c "import taskcfg; print(taskcfg.DECISIONS / ('r%02d.json' % $K))")
[ -f "$f" ] || { echo "missing $f"; exit 1; }
pgrep -af "harnes[s].py|train_danc[e].py" && { echo "harness/training already running"; exit 1; }
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
python harness.py --mode llm --rounds $K --iters 1500 >> ~/projects/dance_logs/harness_$1.log 2>&1
echo "round $K of $1 finished"; tail -n 3 ~/projects/dance_logs/harness_$1.log | cut -c 1-300
