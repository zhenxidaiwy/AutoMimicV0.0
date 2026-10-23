# Round 12 - LLM analysis (step 2; step 3 = decisions/r13.json)

Inputs: analysis/r12_quant.md (automatic), all five every-step sheets 000-187, jump_height.py (pelvis peak robot vs
reference).

## 1. Expectations from decisions/r12.json vs result

| expectation | r11 | r12 | met? |
|---|---|---|---|
| stand_after pelvis speed < 0.3 m/s | 1.19 | 0.14 (eval) | yes |
| stand_after drift < 0.15 m | 0.77 | see E (quiet, on the reference in the sheets) | yes |
| action change < 0.2 | 0.37 | 0.05 | yes (at the "quiet" level) |
| end tilt < 10 | 6.4 | 8.2 | yes |
| rotation >= 345 | 371 | 368 | yes |
| plane deviation < 10 | 5.3 | 9.1 | yes (worse than r11) |
| (not targeted) stand_after deviations | 37 / 54 | 6 / 54 | arm error 6 deg, joint acc ~10 rad/s^2, waist 0.07 rad |

The gate fix removed the shared cause of r09-r11's after-landing failures in one change.

## 2. What the sheets show

| steps | observation |
|---|---|
| 0-39 | on the reference |
| 40-63 | arm raise: the robot's right arm stays horizontal to the side, reference both overhead (shoulder pitch -1.62 vs -2.75, sev 2.1); left foot lifts in 8 of 71 stand steps (sev 2.7) |
| 64-120 | crouch, take-off, tuck, landing on the reference; pelvis peak 1.068 m vs reference 1.108 m (r11 1.176) - the lower "rise" is closer to the reference, not a regression |
| 121-187 | stands upright on the reference, arms down, quiet: the full flow is complete and clean for the first time |

## 3. Assessment

The flow is complete (rotation, airborne, upright landing, quiet stand). What remains is fidelity: arm raise before
the flip, wrists everywhere (sev 3-5; GVHMR hand orientation is unreliable and the wrists do not matter for the
flip on the real robot -> cosmetic), plane 9 deg. This is the point the user defined for the fidelity curriculum:
tighten tracking once the harness judges the flow complete. r09's tightening failed because the balance terms were
missing in the stand; that cause is fixed, so one curriculum step is now justified.

## 4. Priorities

| P | item | why |
|---|---|---|
| P1 | fidelity step: tracking x1.5 -> x2.25, std x0.85 -> x0.722 | curriculum (user), flow complete |
| P2 | arm raise before the flip | visible fidelity gap; aligned with P1 |
| - | wrists | cosmetic, unreliable reference |

## 5. Solution (-> decisions/r13.json)

- tracking.scale 2.25, tracking.std_scale 0.722 (one curriculum step).
- arm pose term for the pre-flip stand (phase stand; after landing the reference also has the arms down), std 0.8
  (error ~1.1 rad -> signal 0.25), weight 2.
- Start from r12 model_10000. Nothing else changes.
- Expect: track_joint_err < 1.6 (r12 1.73), track_body_err < 0.08 m (0.0825), pre-flip right shoulder pitch error
  < 0.6 rad; keep stand_after pelvis speed < 0.3, action change < 0.1, feet off 0, rotation >= 345, upright.
- Rollback: if the stand regresses (pelvis speed > 0.4 or action change > 0.2) or rotation < 340 -> r14 from r12
  model_10000, curriculum back to x1.5 / x0.85, and the stand is investigated before tightening again.
