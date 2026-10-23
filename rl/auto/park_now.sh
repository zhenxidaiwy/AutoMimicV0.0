#!/usr/bin/env bash
# Stop the harness NOW (mid-round) but keep the half-trained round: the next resume.sh continues the same round
# from its latest checkpoint with the same knobs.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; pkill -f "metrics.py"; pkill -f "demo_getup"; sleep 5
pgrep -fa "harness|train_getup|metrics.py|demo_getup" || echo "all stopped"
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
NN=$(printf "%02d" $N)
D=$(ls -d $R/*_auto_r$NN 2>/dev/null | tail -1)
if [ -n "$D" ]; then
  CK=$(ls $D/model_*.pt | sort -V | tail -1)
  mv $D ${D}_part1
  echo "kept half-trained round $N: ${D}_part1 (latest $(basename $CK))"
  ~/miniforge3/envs/gmr/bin/python - "$(basename ${D}_part1)" "$(basename $CK)" <<'EOF'
import json, sys
from pathlib import Path
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
s["warm"], s["warm_ckpt"] = sys.argv[1], sys.argv[2]
(A / "state.json").write_text(json.dumps(s, indent=1))
print("next resume: round", s["round"], "continues from", s["warm"], s["warm_ckpt"])
EOF
  [ -d $A/r$NN ] && mv $A/r$NN $A/r${NN}_part1
fi
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
