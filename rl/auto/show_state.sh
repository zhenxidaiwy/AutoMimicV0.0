#!/usr/bin/env bash
# Harness state at a glance.
grep -a "watchdog" ~/projects/dance_logs/auto/harness.log | tail -2 | cut -c1-250
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
s = json.loads((Path.home() / "projects/dance_logs/auto/state.json").read_text())
b = s["best"]
print("next round", s["round"], "warm", s["warm"], s.get("warm_ckpt"))
print("best", b["round"] if b else None, round(b["score"], 2) if b else None)
print(json.dumps(s["knobs"]))
EOF
