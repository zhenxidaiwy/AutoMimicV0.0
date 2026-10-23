#!/usr/bin/env bash
# The watchdog's generic relaxation targeted the wrong terms (the failure came from the stillness penalties):
# restore round 5's values for them before round 7.
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
s["knobs"].update(w_rise_schedule=-1000.0, w_feet_spread=-120.0, w_squat=11.25, w_joint_speed_cap=-0.2)
(A / "state.json").write_text(json.dumps(s, indent=1))
print(json.dumps(s["knobs"]))
EOF
echo "- (manual) round 7 knobs: the watchdog relaxation (feet_spread, squat, rise_schedule, joint_speed_cap) was reverted to round 5 values - the round-6 failures came from the stillness penalties, not from these terms." >> ~/dance_win/rl/auto/REPORT.md
echo "" >> ~/dance_win/rl/auto/REPORT.md
