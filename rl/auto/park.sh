#!/usr/bin/env bash
# Stop the harness cleanly at a round boundary so it can be resumed with rl/auto/resume.sh:
# wait until the current round is recorded (state.json round advanced), then stop the harness and the training it
# just started, and remove that half-started round (run dir + round folder).
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
cur=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
target=${1:-$((cur + 1))}
for i in $(seq 1 60); do
  now=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
  [ "$now" -ge "$target" ] && break
  sleep 10
done
sleep 5
pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; pkill -f "metrics.py"; pkill -f "demo_getup"; sleep 5
pgrep -fa "harness|train_getup|metrics.py|demo_getup" || echo "all stopped"
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
NN=$(printf "%02d" $N)
for d in $R/*_auto_r$NN; do [ -d "$d" ] && rm -rf "$d" && echo "removed half-started $d"; done
rm -rf $A/r$NN
echo "== state (next round to run: $N)"
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
s = json.loads((Path.home() / "projects/dance_logs/auto/state.json").read_text())
b = s["best"]
print(f"next round {s['round']}, warm start {s['warm']}/{s.get('warm_ckpt')}")
print(f"best so far: round {b['round']} score {b['score']:.2f} {b['ckpt']}" if b else "best: none")
print("next knobs:", json.dumps(s["knobs"]))
EOF
tail -n 4 $A/harness.log | cut -c1-220
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
