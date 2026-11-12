# Round 13 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the same motion as r12. A complete cartwheel that holds still to the end, but it lands crouched with both feet together and the hands still down (72-83) instead of r11's split-leg landing, and robustness to 20 ms latency dropped below the gate.

Inputs: `r13_quant.md`; sheets 000-039, 040-079, 080-119, 720-737 (the hold sheets in between were not opened this round; quant shows pelvis speed 0.00 m/s, drift 0.000 m, action change 0.0001 in the hold).

## Measured, r11 -> r12 -> r13

| metric | r11 | r12 | r13 |
|---|---|---|---|
| robust dr v2 | 0.992 | 0.973 | 0.992 |
| robust 20 ms v2 (gate 0.95) | 0.961 | 0.965 | **0.895 FAIL** |
| robust kp x0.85 v2 (gate 0.95) | 0.988 | **0.914 FAIL** | 0.984 |
| hold tilt error (deg, gate 5) | 4.9 | **5.5 FAIL** | 3.9 |
| jitter:all:settle | 3.38 | 2.2 | 3.3 |
| critic worst unwaived (with the r13 waivers) | 3.38 | - | 4.31 asymmetry:wrist_roll:stand (new) |
| landing | split legs | two-foot crouch | two-foot crouch |

## Diagnosis (corrects r12_llm.md)

- r13 had no asymmetry terms and still lands in the same two-foot crouch. So the r12 diagnosis was wrong: the crouch is not caused by the asymmetry terms. The term r12 and r13 share is `jitter:all:settle`; continued training from r11 is the other common factor. Two rounds cannot separate them.
- `jitter:all:settle` alone did not lower settle jitter (3.38 -> 3.3); in r12 the fall to 2.2 came with the crouch landing.
- The waiver reasons for the two support asymmetry checks stand on their primary grounds (GVHMR orientation of hands / airborne legs; contact works in sim2sim). The secondary reason ("enforcing it changed the landing") is withdrawn.

## Decision

- Rollback rule fires (20 ms v2 0.895 < 0.95): **r11 model_12500 stays the candidate.**
- As set in r13.json: no further agent rounds on the critic. cartwheel_2 stops at r11 with every gate passed (mjlab + sim2sim) except critic 3.38 (`jitter:all:settle`; next `jitter:wrist_roll:land` 3.09). Whether to waive these two jitter checks is the user's decision.
- Budget: 13 rounds, 20.7 GPU-h of 25.
