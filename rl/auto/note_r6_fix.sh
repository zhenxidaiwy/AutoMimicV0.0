#!/usr/bin/env bash
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
## Fix during round 6 (2026-10-21, manual): squat reward hacking - round 6 stopped at ~iteration 24100 and redone

- Symptom (training curve): squat_template rose to 7-9 per s while stand_template fell to ~0 and stand_up from 9.6
  to 5.3 - the robots stayed in the squat for the whole episode.
- Cause: the squat reward had no time limit; with w_squat 16.9 and the standing-only penalties (feet still, torso
  still, arm still) squatting forever paid more than standing up.
- Fix: squat reward only while the rising schedule runs (episode clock < sched_delay + sched_duration); the
  floor_stall penalty now covers any pelvis height below 0.62 m (knob stall_height) after the schedule + 0.5 s.
- Round 6 restarts from round 5 (model_23499) with the same knobs.

EOF
echo noted
