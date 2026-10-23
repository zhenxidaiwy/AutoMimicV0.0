# Round 9 - LLM analysis (step 2; step 3 = decisions/r10.json)

Inputs: analysis/r09_quant.md (auto, incl. new section F2), all five every-step sheets 000-187, training logs r08/r09,
eval_flip.py source (landing metric).

## 1. Expectations from decisions/r09.json vs result

| expectation | r08 | r09 | met? |
|---|---|---|---|
| waist yaw after landing < 0.4 rad | 1.86 | 0.26 | yes |
| hip pitch in flight <= -1.0 | -1.03 mean | -1.74 mean | yes |
| knee over-fold | 2.06 rad | 0.35 rad | yes (not targeted directly) |
| shoulder-yaw asymmetry in flight < 60 deg | 138 | < 1.6 sev (not in top) | yes |
| rotation >= 340 deg | 344 | 358 (323 at the reference landing = on time) | yes |
| plane deviation < 15 deg | 18.5 | 17.0 | no (small gain) |
| action change after landing < 0.2 | 0.30 | 0.41 | **no, worse** |

## 2. What the sheets show

| steps | observation |
|---|---|
| 0-71 (stand, before the flip) | **regression**: the robot does not follow the arm raise (one arm up from step 8, the other out), steps with the left foot (off the floor 41 of 71 steps), drifts beside the reference; r08 stood on the reference here |
| 72-100 | crouch and take-off on the reference |
| 101-118 | best flight so far: tight hip tuck, legs together, rotation in time with the reference |
| 118-143 | lands on both feet, upright, arms near the reference |
| 144-187 | walks sideways away from the reference (pelvis 1.2 m/s, one hop ~45 steps after landing), right arm held out horizontally (shoulder pitch -1.54 vs -0.15), legs scissor; ankles 220 rad/s^2 |

## 3. Causes

1. **Unintended fidelity tightening (found by the new log diff, F2)**: r09 trained with tracking x2.25 / std x0.722,
   r08 with x1.5 / x0.85. The rules set this after r08 (still rules mode) and my r09 decision said "unchanged" without
   checking. Tighter std makes the tracking rewards vanish once the robot is off by a few cm (the same no-gradient
   failure as the templates) - consistent with the pre-flip stand regression and the drift after landing, phases where
   only tracking keeps the robot on the reference.
2. **No pull back after landing**: by design flip_root_pos drops the xy error after the reference lands (r06 walked to
   the reference), and flip_stand_still's velocity term exp(-v/0.2) is 0.002 at 1.2 m/s - no gradient. Hand-written
   fix: velocity scale 0.6 m/s (code change below).
3. **Arms after landing**: arms_stand std 0.5 vs errors up to 1.4 rad -> signal 0.06, too weak.
4. **Trembling / stepping**: nothing rewards both feet staying down while standing (contact checks failing at severity
   7-14 have fixes in the library, never switched on).
5. Metric bug: landing_offset 67 = the hop 45 steps after landing (the metric used the LAST airborne step). Fixed in
   eval_flip.py (end of the first airborne run). Rounds <= 9 keep the old value in their files.

## 4. Priorities

| P | problem | why |
|---|---|---|
| P1 | pre-flip stand regression + walking away after landing + trembling | real robot: stepping / drifting / trembling = unsafe; the flip itself is now good |
| P2 | keep the flight gains | best flight so far - change nothing in flight |
| P3 | plane deviation 17 deg | small; revisit after the stand is fixed |
| - | wrists (sev 2-4.6) | cosmetic |

## 5. Solution (-> decisions/r10.json)

- Revert the tracking curriculum to what r08 trained with (x1.5, std x0.85); the harness will tighten again only by
  decision, after the stand is clean.
- flip_stand_still velocity scale 0.2 -> 0.6 m/s (code), weight 3 -> 4.
- Switch on the library contact fixes for stand and stand_after (both feet), weight 2, and the jitter fix for
  stand_after (dyn_quiet), weight 2.
- arms_stand std 0.5 -> 1.0, weight 3; flight terms (hip_tuck, arms_air) unchanged.
- Expect: pre-flip stand feet off the floor < 5 / 71 steps; after landing pelvis speed < 0.3 m/s, action change
  < 0.2, feet off < 5 / 58; flight held: rotation >= 345, hip mean <= -1.5, over-fold < 0.5 rad.
- Rollback: rotation < 330 or no upright landing -> r11 from r09 model_6999 with only the stand changes.
