# Round 10 - LLM analysis (step 2; step 3 = decisions/r11.json)

Inputs: analysis/r10_quant.md (automatic), all five every-step sheets 000-187, per-step table (tail_table.py on
flip_auto_model_8000_steps.tsv).

## 1. Expectations from decisions/r10.json vs result

| expectation | r09 | r10 | met? |
|---|---|---|---|
| pre-flip stand: feet off < 5 / 71 | 41 (left) | no longer among the deviations; sheets: feet planted | yes |
| after landing: feet off < 5 / 58 | 25 / 12 | 0 / 0 | yes |
| action change after landing < 0.2 | 0.41 | 0.127 (eval 0.14) | yes |
| pelvis speed after landing < 0.3 m/s | 1.2 | 0.44 | no (see 2: a slow squat, not walking) |
| rotation >= 345 | 358 | 353 | yes |
| hip mean in flight <= -1.5 | -1.74 | -1.65 | yes |
| knee over-fold < 0.5 | 0.35 | 0.32 | yes |
| (not targeted) plane deviation | 17.0 | 9.1 | best so far |

Score fell 9.25 -> 7.41 only because stand_stable is false (end tilt 18.3 > 15 deg). By the sheets r10 is the best
policy so far: the score is not the right selector here -> the decider picks the start checkpoint (new `init`).

## 2. What the sheets / per-step table show

| steps | observation |
|---|---|
| 0-39 | on the reference, arm raise slightly behind |
| 40-63 | arms up but asymmetric (left shoulder pitch -1.55 vs ref -2.69, sev 2.6); feet planted |
| 64-100 | crouch / take-off on the reference |
| 101-119 | tight tuck, legs together, in plane (9 deg), on time |
| 120-150 | lands both feet, upright by step 132 (tilt 8 -> 4 deg, ref 9 -> 2), stands next to the reference |
| 152-183 | slowly sinks into a squat and leans: knees 0.41 -> 0.82 (ref 0.06), pelvis 0.78 -> 0.72 m, tilt 7 -> 20 deg, feet 0.18 -> 0.35 m apart; right arm held forward (shoulder pitch -1.21 vs -0.15) as a counterweight |
| 184-187 | knees extend again (0.45) |

## 3. Causes

1. Nothing asks for straight legs once standing: flip_stand_still uses the mean error over all 29 joints / 0.2, a
   0.75 rad error on two knees moves that mean by only ~0.05 rad; tracking (std x0.85) and stand_quiet tolerate a
   slow sink. The squat is a cheap stable posture under the new contact / quiet rewards.
2. The forward arm compensates the forward lean (centre of mass over the feet); it should disappear with the lean.
3. term_stand_fail allows 30 deg tilt, 0.45 m feet.

## 4. Priorities

| P | problem | why |
|---|---|---|
| P1 | squat + lean 16-20 deg after landing | stand quality on the real robot (knee torque held at 0.8 rad, falls if it continues) |
| P2 | arm forward after landing | likely follows P1; re-check next round |
| P3 | pre-flip arm raise asymmetric (sev 2.6) | cosmetic for the flip; tighten tracking later |
| - | wrists (sev 2-4.7) | cosmetic |

## 5. Solution (-> decisions/r11.json)

- Start from r10 model_8000 (not the best-score r09 model_6999).
- Leg posture after landing: dyn_joint knees + hip pitch + ankle pitch, phase stand_after, std 0.4 (current error
  ~0.7 rad -> signal 0.17), weight 3.
- term_stand_fail max_tilt 30 -> 25 deg (stand_after only; r10 peaks at 20, so it bites only on a real fall-over).
- Everything else unchanged (flight and the r10 stand fixes work).
- Expect: end tilt < 10 deg, knees in stand_after < 0.3 rad, pelvis > 0.76 m, stand_stable true; keep feet off 0,
  action change < 0.2, rotation >= 345, plane deviation < 12.
- Rollback: rotation < 330 or no upright landing -> r12 from r10 model_8000 without the leg term.
