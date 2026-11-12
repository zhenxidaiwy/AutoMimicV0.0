# Round 1 (cartwheel_2): LLM analysis (step 2)

Inputs:
- `r01_quant.md` (step 1);
- the round video `videos/cartwheel_2/auto/r01/r01_model_1000.mp4`;
- all 13 every-step sheets (000-487, reviewed frame by frame);
- the training log `train_cw2auto_r01.log`.

Extra checks run for this analysis:
- `ref_term_audit.py` (the reference against the terminations and the absolute rewards);
- `ref_selfcollide.py` / `ref_feet_z.py` (the reference in the training model);
- `round_dig.sh` (arm joints, robot vs reference).

## What the frames show

| steps | reference (green) | robot (white) |
|---|---|---|
| 0-7 | stands with arms overhead | tracks |
| 4-23 | arms stay overhead (shoulder pitch -1.8 rad) | swings both arms down and back: left shoulder pitch -1.5 -> +2.68 rad by step 16 (joint upper limit 2.67), right +1.2 |
| 24-47 | lunges sideways, hands go to the floor, legs start over | keeps the arms back, hops on the feet, leans sideways; no hand reaches the floor |
| 48-60 | inverted on the hands, legs vertical | falls on its side (step 48-56) instead of going over |
| 60-240 | lands one foot after the other, stands in a wide stance | lies on the floor and rolls / kicks; never stands up |
| 240-487 (+5 s) | holds the final pose | keeps thrashing on the floor (legs kicking up at 400-487) |

The 231 deg "rotation" that passes the rotation gate comes from rolling on the floor, not from a cartwheel. `landed_upright` False, end pelvis 0.175 m.

## Causes, measured

**1. Two aerial-family terminations fire on the reference itself.**
- Frames 81-90 are the first 0.2 s of `land`.
- `term_flight_spread` (feet > 0.6 m) fires on all 10 of them: the reference's feet are 0.62-0.65 m apart.
- `term_leg_twist` (knee separation > 0.45 m, |hip roll| > 0.6) also fires on all 10: knee separation 0.45-0.48 m, hip roll up to 0.74.
- So every rollout that does the cartwheel correctly is terminated at touch-down, and every RSI start in that window dies immediately.
- A cartwheel lands in a straddle. These limits encode the backflip's tucked, feet-together landing, and r01 inherited them because the harness applies its default terminations to every task.

**2. Aerial-family rewards with absolute targets pay the reference little.**
- What the reference earns inside each term's own gate:
  - `flip_leg_sym` (legs mirror-symmetric in the landing window): 0.04;
  - `flip_land_balance` (pelvis over the ankle midpoint): 0.62;
  - `flip_land`: 0.87, with 0 only in frames 81-83, where one foot is still in the air.
- Logged reward magnitudes at the end of r01:
  - backflip-family terms: `flip_feet_together` 1.11, `flip_stand_still` 0.71, `flip_land` 0.48, `flip_land_balance` 0.44;
  - tracking terms: `motion_body_pos` 0.26, `motion_body_ori` 0.08.
- So the landing / standing terms dominate the tracking signal.

**3. The reference floats one foot in both still stances.**
- In the training model, the left sole is 2.8-3.8 cm above the floor in the first stand (frames 0-9, 30 fps).
- The right sole is 2.4-3.1 cm up for the whole held final pose (2.5 s).
- In both cases the floating leg is fully straight: knee 0.01-0.08 rad, hip-to-ankle 0.658 m = straight length. The other knee is bent 0.6-0.8 rad.
- `ground_fix` moves only the root, so this cannot be fixed without lowering the pelvis.
- With this reference, "stand still on both feet for 2 s" would be impossible.

**4. Termination storm.**
- Mean episode length was 12.7 steps at the start and 146 at the end.
- `ee_body_pos` (threshold 0.6 m) is the dominant termination: about 15 per log line, against 1-6 for each of the others.
- The arms-back strategy (wrist z error about 1 m) shows the policy never learned the lunge. Episodes that try it are cut by cause 1, so the policy had no reason to learn the hand support.
- Not changed this round: first remove the terminations that contradict the reference, then re-measure.

**5. Score.**
- The round score is the aerial one (airborne time / 0.35 s, pelvis rise / 0.15 m, rotation / 300 deg).
- It is meaningless for a cartwheel. Checkpoint selection used it.

Checked and ruled out:
- The reference has no robot self-contact in the training model, so the overhead arms are reachable.
- The arm joints are within limits.
- Hand friction, delay and terminations were applied as decided (quant F).

## Solution for round 2

1. **Terminations:** `term_flight_spread` and `term_leg_twist` off (null), because they fire on the reference. `term_hip_extended` is gated on `flight`, which does not exist in this clip, so it stays inactive. `term_stand_fail` is kept (fires 0 frames on the reference).
2. **Rewards:** weights 0 for the terms that pay the reference < 0.8 in their gate:
   - `flip_leg_sym` (0.04);
   - `flip_land_balance` (0.62).

   The terms whose gates never open in this clip have no effect and stay as they are. The reference-relative terms stay. `flip_land` (0.87) stays.
3. **Reference:** switch to `plant_vlm_hold`. This is `feet_plant.py`, a new generic repair:
   - planted feet are made level, with the sole at z = 0, in the stand phases;
   - only the legs and the root height change; knees are kept >= 0.1 rad;
   - root xy, orientation, waist and arms are unchanged (max change 0.0);
   - root lowered by at most 5.5 cm (first stand) and 4.7 cm (final stand);
   - planted soles go from 3.75 / 3.13 cm to 0.31 / 0.11 cm;
   - QA render against GVHMR checked at t = 0.1 / 0.25 / 2.3 / 2.55 s: both feet down, arms and palms unchanged.
4. **Start from scratch:**
   - the r01 policy learned a fall-sideways strategy under the wrong terms;
   - its value function is trained on episodes truncated at the landing.
5. **Generic guard in the harness:**
   - before training, `ref_audit` runs the reference against the round's terminations and refuses the round if any active one fires on it;
   - the audit (including what the absolute rewards pay the reference) is stored in the round record.
6. **Score:** family-aware. Non-aerial families use rotation relative to the reference, landed upright, stand stable and no fall in the hold.
7. **Library:**
   - generic lessons: `ref-passes-terminations`, `rewards-pay-the-reference`, `planted-feet-on-floor`, `family-score`;
   - `family:hand_support` lessons: `arms-by-position`, `palms-down`, `hand-grounding`, `hand-friction`, `wide-stance-termination`.

## Expected after round 2

- No reference-contradicting termination: `term_flight_spread` / `term_leg_twist` counts are 0 in the log.
- The robot gets past step 48 without falling sideways and reaches the hand support (hand_L / hand_R contact in support).
- Rotation from going over, not from rolling: `landed_upright` is the real test. It may still fail after one round from scratch.
- Mean episode length at the end of the round > 146.

Rollback: if the robot still falls sideways before the support phase and the episode length does not grow, the next round looks at the `ee_body_pos` termination and the RSI prior of the lunge / support phases.
