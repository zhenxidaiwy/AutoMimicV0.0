#!/usr/bin/env bash
# Round 9 just started: stop it, add the widened stillness kernel (still_sigma_scale 3), smoke test, restart later.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
for d in $R/*_auto_r09; do [ -d "$d" ] && rm -rf "$d" && echo "removed $d"; done
rm -rf $A/r09
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
s["knobs"]["still_sigma_scale"] = 3.0
(A / "state.json").write_text(json.dumps(s, indent=1))
EOF
bash ~/dance_win/rl/auto/show_state.sh | tail -3
bash ~/dance_win/rl/auto/stop_now.sh 2>&1 | grep -E "smoke|exit|Error|Traceback"
grep -E "Episode_Reward/still_bonus" ~/projects/dance_logs/auto_smoke.log | tail -1
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
- (manual, before round 9) still_bonus kernels widened 3x (still_sigma_scale 3: 0.15 m/s, 0.9 rad/s, 3 (rad/s)^2):
  in round 8 the bonus paid 0.14 of max 6 - under the training action noise the narrow kernels were ~0 everywhere.

EOF
