# Round 11 - LLM analysis (step 2; step 3 = decisions/r12.json)

Inputs: analysis/r11_quant.md (automatic; section E now per label segment), all five every-step sheets 000-187,
stand_trace.py (phase label, drift and pelvis speed per step), flip_rewards.py gates.

## 1. Expectations from decisions/r11.json vs result

| expectation | r10 | r11 | met? |
|---|---|---|---|
| end tilt < 10 deg | 18.3 | 6.4 | yes |
| knees straight in stand_after | 0.8 rad | straight on the sheets | yes |
| stand_stable | false | true | yes |
| rotation >= 345 | 353 | 371 | yes |
| plane deviation < 12 | 9.1 | 5.3 | yes (best so far) |
| action change < 0.2 | 0.14 | 0.37 | **no** |
| feet off 0 | 0 | 4 / 0 | almost |

## 2. What the sheets / trace show

| steps | observation |
|---|---|
| 0-79 | best pre-flip so far: arms raised symmetrically on the reference, feet planted |
| 80-120 | take-off, tight tuck, legs together, plane 5 deg |
| 121-154 (land, settle) | upright, legs straight, next to the reference, speed 0.3 m/s |
| 155-187 (stand) | starts walking sideways, speed 0.5 -> 1.97 m/s, drift 0.77 m, right arm out |

## 3. Cause (found by matching the onset with the label switch)

The walk-off begins exactly at the settle -> stand label switch (step 155). r10's squat began at step 152 and r09's
walk-off at ~144-155: the same switch. In flip_rewards.py, flip_land_balance (CoM over the feet, weight 3 x 2),
flip_feet_together and flip_land (upright, both feet down) are gated to land / settle only, so from step 155 nothing
keeps the CoM over the feet; the robot starts to fall slowly and steps to catch itself. Each round I added a term for
the symptom (r10 stand_still velocity, r11 straight legs) instead of the shared cause. Lesson recorded: check where a
failure starts relative to the label / reward-gate boundaries (quant report section E now prints per segment).

## 4. Priorities

| P | problem | why |
|---|---|---|
| P1 | walk-off after the settle -> stand switch | the last blocker for a usable flip; one cause behind r09-r11 |
| P2 | arm held out after landing | likely balance compensation; re-check after P1 |
| - | wrists (sev 2-5) | cosmetic |

## 5. Solution (-> decisions/r12.json)

- Code: flip_land, flip_feet_together and flip_land_balance also act in stand_after (stand frames after the reference
  landing). No weight changes, nothing else changed.
- Start from r11 model_9499 (best score and best policy).
- Expect: stand_after pelvis speed mean < 0.3 m/s, drift < 0.15 m, action change < 0.2, end tilt < 10, rotation >= 345,
  plane < 10.
- Rollback: rotation < 330 or no upright landing -> r13 from r11 model_9499 with the gate change only on land_balance.
