#!/usr/bin/env bash
~/miniforge3/envs/gmr/bin/python -m py_compile ~/dance_win/rl/auto/harness.py && echo "harness ok"
cat >> ~/dance_win/rl/auto/REPORT.md <<'EOF'
## Root cause of the repeated collapses (2026-10-21 16:30, controlled tests)

- Rounds 6 (three attempts) and 7 all collapsed within ~50 iterations (robots on the floor). Controlled tests:
  the round-5 policy, run WITHOUT learning in the training config (with sampled actions), stands 100%; resuming
  training from it with the exact round-5 config (test A) or from its intermediate checkpoint (C) collapses too,
  while resuming from round 4 (D, round 5's own start) does not.
- Decisive test: resume from round 5 without random initial episode clocks: lr 1e-3 (E1) collapses
  (stand_up 0.95, floor_stall -4.25), lr 3e-4 (E2) stays healthy (stand_up 9.6, floor_stall -0.02).
- Cause: rsl_rl's adaptive learning rate is not stored in checkpoints; every warm start restarted at lr 1e-3,
  too large for a converged policy - whether a round survived was luck. The reward explanations given for
  attempts 6b / 6c / 7 were therefore at most secondary (6a's squat hacking was a real reward exploit).
- Fix: every round now starts at lr 3e-4 (harness --lr) with GETUP_NO_RANDOM_EP_LEN=1. The stillness bonus and
  the other reward changes are kept (they are sound designs); round 8 continues from round 5.

EOF
echo noted
