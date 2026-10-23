#!/usr/bin/env bash
# Stop round 6, set moderate stillness weights for the redo (time-gated now), smoke test, note in the report.
A=~/projects/dance_logs/auto
bash ~/dance_win/rl/auto/stop_now.sh > /dev/null 2>&1
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
s["knobs"].update(w_feet_move_stand=-45.0, w_torso_still=-10.0, w_arm_still=-0.5, stillness_time_only=True)
(A / "state.json").write_text(json.dumps(s, indent=1))
print("round", s["round"], "from", s["warm"], s.get("warm_ckpt"), "knobs", json.dumps(s["knobs"]))
EOF
bash ~/dance_win/rl/auto/stop_now.sh 2>&1 | grep -E "smoke|exit|Episode|Error|Traceback"
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
## Fix 2 during round 6 (2026-10-21, manual): gate exploitation - round 6 redone again

- Symptom (redo with the time-limited squat reward): stand_up 5-6.6, standing_posture / stance / feet_planted /
  stand_template ~0, floor_stall -4.2/s - robots crouched at pelvis 0.55-0.6 m, just under the 0.65 m
  "standing" gate (even the 40% standing starts left the stance).
- Cause: feet_move_stand / torso_still / arm_still only applied while "standing tall" (pelvis > 0.65 m, upright);
  with their weights raised (-67.5 / -15 / -1.5) not standing became the cheapest way out of all of them. Same
  pattern as round 3 (a state gate that can be escaped).
- Fix: these three penalties are now gated by the episode clock (schedule end + 0.5 s = 3.5 s) and "not fallen"
  (pelvis > 0.4 m) only, with the push grace kept; redo uses moderate weights (-45 / -10 / -0.5).
- The harness watchdog (stand_up < 8 for 200 iterations -> stop the round) is now in place for such collapses.

EOF
echo noted
