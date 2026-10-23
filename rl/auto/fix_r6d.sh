#!/usr/bin/env bash
# Stop round 6 (attempt 3), switch to the stillness bonus, smoke test, note in the report.
bash ~/dance_win/rl/auto/stop_now.sh > /dev/null 2>&1
~/miniforge3/envs/gmr/bin/python -m py_compile ~/dance_win/rl/auto/harness.py && echo "harness ok"
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json
from pathlib import Path
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
s["knobs"].update(w_feet_move_stand=-45.0, w_torso_still=0.0, w_arm_still=0.0, stillness_time_only=False,
                  w_still_bonus=6.0)
(A / "state.json").write_text(json.dumps(s, indent=1))
print("round", s["round"], "from", s["warm"], s.get("warm_ckpt"))
EOF
bash ~/dance_win/rl/auto/stop_now.sh 2>&1 | grep -E "smoke|exit|Episode|Error|Traceback"
grep -E "Episode_Reward/still_bonus" ~/projects/dance_logs/auto_smoke.log | tail -1
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
## Fix 3 during round 6 (2026-10-21, manual): stillness as a bonus, not a penalty - round 6 redone a third time

- Symptom (attempt 3, clock-gated stillness penalties excluding pelvis < 0.4 m): within ~50 iterations from the
  round-5 policy (100% get-up) almost all robots lay on the floor (floor_stall -4.5/s, stand_up 0.25); later the
  policy flailed (arm_still -11/s, feet -13/s, action std 0.41 -> 0.84).
- Cause: "pelvis < 0.4 m is exempt" was one more escape hatch - lying down avoided every stillness penalty.
  Lesson (rounds 3, 6a, 6b, 6c): a penalty attached to a desired state (standing) teaches the policy to leave it.
- Fix: torso_still / arm_still / clock gating removed (weights 0); new POSITIVE bounded term still_bonus (w 6),
  paid only while standing tall: mean of exp(-(torso speed/0.05)^2), exp(-(torso ang. speed/0.3)^2),
  exp(-(sum arm joint speed^2)/1). Leaving the stance only loses it. feet_move_stand back to the round-5 form (-45).
  The sway rule now raises w_still_bonus (x1.3, max 15).

EOF
echo noted
