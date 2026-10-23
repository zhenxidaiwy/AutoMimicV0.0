# Round 15 - LLM analysis (step 2; step 3 = decisions/r16.json)

Inputs: analysis/r15_quant.md (automatic, incl. A2 robustness and the new section S stop criteria - the r15 critic
was re-run on library v2), all five every-step sheets 000-187, sim2sim report of r14 (sim2sim/results_flip.md).

## 1. Expectations from decisions/r15.json vs result

| expectation | r14 | r15 | met? |
|---|---|---|---|
| latency 20 ms success >= 0.95 | 0.695 | 0.992 | yes |
| latency 40 ms success >= 0.5 | 0.0 | 0.223 | no |
| nominal / DR / stiffness 1.0 | 1.0 | 1.0 / 1.0 / 1.0 | yes |
| body tracking error < 0.075 m | 0.064 | see A (r15 worse than r14 by 9 %) | held loosely |
| rotation >= 345 | 365 | 367.5 | yes |
| action change after landing < 0.1 | 0.053 | 0.185 | **no** |

## 2. Sheets
0-39 on the reference; 40-63 arm raise again with the robot's right arm sideways (cosmetic, seen in r12 too);
64-120 crouch / take-off / tuck / landing as r14; 121-187 upright, both feet down, close to the reference - the
regression in quietness is not visible in the sheets (pelvis speed 0.27 m/s mean, drift 0.16 m over 0.66 s, action
change 0.185): a slow sway, not stepping.

## 3. Causes
1. Latency training changes the control problem; with a 25 ms lag the policy corrects later and more.
2. A bug in the latency implementation (found by the sim2sim agent, confirmed by test_delay_fix.py): mjlab's delay
   buffer backfills a reset row with the first target after the reset, which is all zeros, so every episode began
   with 1-5 physics steps commanding 0 rad on every joint - a jolt at each start, including the many episodes that
   start standing or settling (phase-weighted starts). Fixed in rl/mimic_generic.add_action_delay (hold pose).
   Lesson: generic (any skill trained with latency).
3. The 40 ms target was not required by the stop criteria (real G1 latency ~10-20 ms) - dropped as a goal.

## 4. Stop criteria (section S, first evaluation)
not done: quiet / still after landing fail; critic_clean fails only on wrist checks (worst
backflip_3/asymmetry:wrist_roll:crouch 6.4) - GVHMR hand orientation is unreliable and the wrists do not matter
for the flip -> waived with reason; in_plane 11.2 deg vs 10; sim2sim pending (r14 passed nominal 100 %, latency
20 ms 90 % - the exam is run again once the other gates pass); not converged.

## 5. Decision (-> decisions/r16.json)
- The delay fix is the only training change (it is active automatically through train_dance --delay-ms 25).
- Waive the wrist checks of this task (cosmetic, unreliable reference).
- Start from r15 model_13499.
- Expect: action change after landing <= 0.1, pelvis speed <= 0.1 m/s; latency 20 ms >= 0.95 held; rotation >= 345.
- If quietness does not recover: next round raises stand_quiet / stand_still (they were 3 / 4 x2).
