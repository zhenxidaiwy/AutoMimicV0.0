#!/usr/bin/env bash
# snapshot_rules.sh: freeze the rules-mode run (rounds 1..8) before switching to LLM mode, for the later comparison.
# Copies harness state, diagnostic library, report, per-round dyn configs and the code into runs/rules_v1_r01-r08/.
cd ~/dance_win/rl/flip_auto || exit 1
D=runs/rules_v1_r01-r08
[ -e "$D" ] && { echo "$D exists, not overwriting"; exit 1; }
mkdir -p "$D/code"
cp state.json library.json REPORT.md "$D/"
cp dyn_r*.json "$D/" 2>/dev/null
cp harness.py library.py critic.py task_init.py ../flip_rewards.py ../eval_flip.py ../train_dance.py "$D/code/"
ls ~/projects/dance/runs/logs/rsl_rl/g1_tracking/ | grep flipauto_r > "$D/run_dirs.txt"
chmod -R a-w "$D"
echo "snapshot -> $D"; ls "$D"
