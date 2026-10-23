# Round 13 - LLM analysis (step 2; step 3 = decisions/r14.json)

Inputs: analysis/r13_quant.md (automatic), all five every-step sheets 000-187.

## 1. Expectations from decisions/r13.json vs result

| expectation | r12 | r13 | met? |
|---|---|---|---|
| track_joint_err < 1.6 | 1.73 | 1.52 | yes |
| track_body_err < 0.08 m | 0.0825 | 0.073 | yes |
| pre-flip right shoulder pitch error < 0.6 rad | ~1.1 | no longer among the stand deviations; sheets: both arms overhead | yes |
| stand pelvis speed < 0.3 | 0.14 | 0.047 | yes |
| action change < 0.1 | 0.05 | 0.039 | yes |
| feet off 0 | 0 | 0 (no contact deviation listed) | yes |
| rotation >= 345, upright | 368 | 367, upright, end tilt 2.9 | yes |

No rollback condition hit: the curriculum step worked this time (the r09 failure was the balance-gate bug, fixed in r12).

## 2. Sheets

| steps | observation |
|---|---|
| 0-79 | robot overlaid on the reference, arm raise with both arms overhead |
| 80-120 | take-off, tuck, landing as r12; pelvis peak 1.148 m (ref 1.108) |
| 121-187 | upright, quiet; from ~152 the robot overlaps the reference almost exactly, including position |

## 3. Remaining deviations (all fidelity)

- wrists in every phase (sev 2-5): GVHMR hand orientation is unreliable; no effect on the flip -> cosmetic.
- take-off: left shoulder yaw 73 deg off (sev 4.9); landing: right shoulder pitch 45 deg (sev 3.0).
- plane deviation 9.3 deg (stable since r12).

## 4. Decision

- Continue the curriculum one more step: tracking x3.375, std x0.614 (same factor as r13's step). Arms at take-off /
  landing are tracking errors, so this is the matching tool.
- Start from r13 model_11499; nothing else changes.
- Expect: track_joint_err < 1.4, track_body_err < 0.065 m, take-off shoulder-yaw sev < 3; keep stand pelvis < 0.3,
  action change < 0.1, rotation >= 345, upright.
- Rollback: stand regresses (pelvis speed > 0.3 or action change > 0.15) or rotation < 340 -> r15 from r13 model_11499
  at x2.25 / x0.722, curriculum considered converged.
- Next after the curriculum: robustness (randomised friction / mass / pushes, MuJoCo CPU sim2sim) matters more for the
  real G1 than wrist fidelity.
