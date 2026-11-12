# Round 12 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** a complete cartwheel that holds still for the whole 5 s tail, but worse than r11: it lands in a crouch with both feet together and the hands still on the floor (72-83), then stands up on one leg for a few frames (84-90). r11 landed in the reference's split-leg landing.

Inputs: `r12_quant.md` (A, A2, A3, B, C, S), `round_look.sh cartwheel_2 12 model_13500` (floor contacts, ankle z, labels), close-ups 48-59, 60-71, 72-83, 84-95, 96-107 (full resolution), all 19 sheets 000-737.

## Frame by frame (model_13500)

| frames | what the robot does |
|---|---|
| 0-23 | stands with arms overhead; the left knee bends 0.20 -> 0.74 rad while the reference keeps it at 0.06-0.11 (same as r11); the left ankle rises at most 1.5 cm, so the foot stays down |
| 24-47 | lunge; the left hand reaches the floor at step 46 (reference 53) |
| 48-59 | straight-arm support, still ahead of the reference: inverted at 56-58 while the reference is at about 45 deg; legs split in the air |
| 60-71 | both palms down (wrist_yaw contact 46-73 left / 52-76 right vs reference 53-69 / 58-72); the legs come over the top together, not one after the other |
| 72-83 | **new fault:** the robot lands crouched over its feet with both hands still on the floor (right foot down 71-84, hands until 73/76), while the reference is still in the split-leg cartwheel with one leg up |
| 84-90 | rises with the left knee lifted (left ankle 0.10 m at step 86) and the arms forward; stance narrower than the reference |
| 91-131 | upright, arms go overhead, final pose reached about frame 104; hold tilt error 5.5 deg (gate 5) |
| 132-737 | no visible motion on any sheet (pelvis speed max 0.00 m/s, drift 0.000 m in the hold window) |

## Measured, r11 -> r12

| metric | r11 | r12 |
|---|---|---|
| robust dr v2 | 0.992 | 0.973 |
| robust 20 ms v2 | 0.961 | 0.965 |
| robust kp x0.85 v2 (gate 0.95) | 0.988 | **0.914 FAIL** |
| robust 40 ms v2 (not a gate) | 0.453 | 0.582 |
| hold tilt error (deg, gate 5) | 4.9 | **5.5 FAIL** |
| tracking body error (m) | 0.056 | 0.048 |
| rotation (deg, reference 255.5) | 291.4 | 256.0 |
| critic worst unwaived (gate 3) | 3.86 asymmetry:wrist_roll:support | **5.19** jitter:wrist_roll:land |
| asymmetry:wrist_roll:support / hip_yaw:support | 3.86 / 3.23 | below 1 (fixed) |
| jitter:all:settle | 3.38 | 2.2 |

## Diagnosis

> Correction after r13 (see r13_llm.md): r13 had no asymmetry terms and still landed in the same crouch, so the
> attribution of the crouch to the asymmetry terms below is wrong; the shared factor is `jitter:all:settle` and/or
> continued training from r11.

- The two asymmetry fixes worked on their own checks (both no longer fail), and the settle jitter fell 3.38 -> 2.2. But the policy got there by changing the whole support-to-landing motion: the legs come over together and it lands in a crouch with both feet, which costs the stiffness robustness (0.988 -> 0.914), hold tilt (4.9 -> 5.5) and the wrist jitter on land (3.09 -> 5.19 even at weight 2).
- The rollback rule set at r12's launch fires (kp v2 < 0.95 and hold tilt fails): **r11 model_12500 stays the candidate.**

## Waiver review of r11's remaining checks (rule: review one by one, no new terms)

| check | r11 | decision | reason |
|---|---|---|---|
| asymmetry:wrist_roll:support | 3.86 | **waive** | The reference's palm orientation in support is not ground truth (GVHMR hand orientation + the palm-down repair in the retarget). The hand contact that matters works: 100/100 in sim2sim at hand friction 0.5 and 1.0, and robust dr 0.992. Enforcing it (r12) cost kp robustness and hold tilt. |
| asymmetry:hip_yaw:support | 3.23 | **waive** | Leg twist while the legs are in the air above the head, estimated by GVHMR from an inverted pose. It has no contact consequence; enforcing it together with the wrist term changed the landing (r12). |
| jitter:all:settle | 3.38 | keep | Action rate during the stand-up matters on the real G1 (motor heating, actuator bandwidth). Its fix reduced it in r12 (3.38 -> 2.2); the r12 regressions are explained by the asymmetry terms, which change the support motion, not by a quiet term in settle. Test it alone. |
| jitter:wrist_roll:land | 3.09 | keep | Same reason (real-hardware jitter). Weight 2 in r12 did not help; back to r11's weight 1. |

Precedent: backflip_3 r16 waived `*wrist*` as unreliable GVHMR hand orientation.

## Decision for round 13

- init r11 `model_12500`, all r11 knobs.
- Library weights back to r11 (they persist across rounds in library.json): `asymmetry:wrist_roll:support` 0, `asymmetry:hip_yaw:support` 0, `jitter:wrist_roll:land` 1. The only change from r11: `jitter:all:settle` 1.
- Waive the two asymmetry checks above. With the waivers, r11's critic is 3.38 (jitter:all:settle).
- Rollback: if any robust v2 gate < 0.95 or any hold gate fails, r11 model_12500 stays the candidate. In that case the jitter checks are not waived by the agent: cartwheel_2 stops at r11 with critic 3.38 and the remaining decision (waive jitter or accept) goes to the user.
- If r13 passes every mjlab gate: sim2sim exam on r13 (same suite as r11).
