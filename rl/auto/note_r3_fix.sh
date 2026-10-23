#!/usr/bin/env bash
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
## Fix before round 4 (2026-10-21 13:10, manual): round 3 collapsed (success 23%)

- Symptom: from supine / face-down / right side the robots sat at pelvis 0.17 m with the legs wide open for the whole
  episode (left side still stood up). The collapse showed within the first 100 iterations of round 3.
- Cause 1, reward cliff: feet_spread switched on at once when the pelvis passed 0.2 m (w -120): rising from a
  wide-legged sit cost ~24/s immediately, so sitting just below 0.2 m became a local optimum.
  Fix: the gate ramps from 0 at 0.2 m to 1 at 0.45 m (knob feet_spread_ramp).
- Cause 2: feet_move_stand also fired while catching the random training pushes (~10.6/s in round 2, half of the
  standing reward), making standing less attractive. Fix: only while the pelvis moves < 0.15 m/s horizontally
  (knob feet_still_body_speed) - stepping without a reason is still penalised.
- New term floor_stall (w -5): pelvis still below 0.4 m 0.5 s after the rising schedule has ended.
- Round 4 restarts from round 2 (model_20999) with the half-step knobs.

EOF
echo noted
