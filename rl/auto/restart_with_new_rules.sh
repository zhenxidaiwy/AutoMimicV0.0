#!/usr/bin/env bash
# Stop the harness (and its current training), recompute the next round's knobs from the best round's metrics with
# the current (edited) rules in harness.py, drop the half-started round's run dir, and start the harness again.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/start.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
pgrep -fa "harness|train_getup" || echo "stopped"
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "dance_win/rl/auto"))
import harness as h
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
b = s["best"]
m = json.loads((A / f"r{b['round']:02d}" / "metrics.json").read_text())
k, ch = h.adjust(b["knobs"], m)
s["knobs"] = k
s["warm"] = b["run"]
(A / "state.json").write_text(json.dumps(s, indent=1))
print(f"next round {s['round']} from {b['run']}:"); print("\n".join(ch))
EOF
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
for d in $R/*_auto_r$(printf "%02d" $N); do [ -d "$d" ] && rm -rf "$d" && echo "removed half-started $d"; done
rm -rf $A/r$(printf "%02d" $N)
