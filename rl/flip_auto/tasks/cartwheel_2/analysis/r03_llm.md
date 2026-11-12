# Round 3 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the robot now does the whole cartwheel from standing and lands upright, holding the final pose quietly for 2 s + 5 s. But it goes over on its head and forearms (elbows bent, head on the floor), not on straight arms like the reference.

Inputs:
- `r03_quant.md` (A, A2, A3);
- all 13 every-step sheets (000-487);
- full-resolution close-ups of every frame 0-131 (`videos/cartwheel_2/auto/r03/close/`, 4 frames per row, `closeup.sh`), which is new this round;
- `floor_contacts.py` (bodies within 1 cm of the floor, robot vs reference);
- `body_min_z.py` and arm joint tables.

## Frame by frame

| frames | reference | robot (close-ups) |
|---|---|---|
| 0-11 | stands on both feet, arms overhead | arms overhead, tracks; one foot lifted from frame 1 (left ankle off the floor 1-22; reference down 0-22) |
| 12-35 | shifts sideways into the lunge | follows with a lateral lag of a few tenths of a metre; arms spread, wide stance |
| 36-47 | torso goes horizontal, hands towards the floor | torso horizontal, legs swing up; elbows already bending (left elbow 1.04 -> 0.35 rad at 44-48, reference 1.4) before any hand touches |
| 48-71 | inverted on straight arms, palms on the floor, head about 0.4 m up | inverted with the head on the floor (torso_link contact 54-58, 61-62), both forearms / elbows on the floor (54-67), shoulders 55-57; elbows down to -0.46 rad (reference 1.38) |
| 72-95 | lands foot after foot, comes up | on hands and feet, rises, comes up |
| 96-131 | settles into the wide final stance, arms overhead | same pose, upright, arms overhead |
| 132-487 | holds | holds still: no visible sway, small constant offset beside the reference |

## Measured

**Big step forward from r02:**
- Rotation 254.5 deg vs reference 255.5.
- `landed_upright` True, end tilt 15.8 deg, end pelvis 0.725 m.
- Track body error 0.69 -> 0.088 m.
- After the reference: drift 0.007 m, sway 0.004 m, action change 0.0008.
- In the 2 s hold: no fall, tilt error 5.3 deg, pose error 0.098 rad.

**Segment probe:** never lost from frame 0: 0.78. From frames 16 / 30 / 46 / 60 / 95 / 115: 0.86 / 0.95 / 1.0 / 0.88 / 1.0 / 1.0. Only the land start (frame 81) is weak (0.39).

**Robustness:**

| scenario | success |
|---|---|
| nominal | 0.99 |
| training randomisation | 0.75 |
| +20 ms delay | 0.65 |
| +40 ms delay | 0.08 |
| PD x0.85 | 0.66 |

The gate is 0.95.

**The shortcut:**
- In support (steps 40-90), the robot's pelvis, torso, shoulders and elbows are 0.18-0.22 m below the lowest height the reference ever gives them. For example, elbow minimum 0.03 m vs reference 0.24 m.
- Floor contacts: robot torso (head) 7 steps, elbows 14 / 10, shoulders 2 / 3. The reference has only the wrists (palms).
- The elbow bending starts in the air (frames 44-52), so the arms are not buckling under load: the policy chooses to lower the body onto head and forearms. A tripod of head + forearms is more stable than a straight-arm inversion.
- The tracking rewards tolerate it, because their errors are relative and of the order of 0.2 m. No termination covers bodies other than the feet and hands (`ee_body_pos`).
- On a real G1 this is a head impact. It is also not the skill in the video.

**Not visible in the sheets:** at sheet resolution (~250 px per tile) the head contact looked like a hand support. The close-ups and the contact list showed it. This is the reason for the new `closeup-review` lesson.

## Solution for round 4

1. **Termination `term_below_reference` (new, generic, `rl/mimic_generic.py`, margin 0.12 m):**
   - Terminate when any tracked body is lower than the reference's own minimum height for that body minus 0.12 m.
   - Bodies whose threshold would be under 5 cm (feet, hands: the contact bodies) are not checked.
   - The reference passes by construction (guard).
   - On r03's policy, it would fire on pelvis, torso, shoulders and elbows in support. The thresholds are, for example: elbows 0.12 m, shoulders 0.26-0.28 m, torso 0.52 m.
2. **Warm start** from r03 `model_2998`: keep the chain, the landing and the quiet hold.
3. **Library:** generic lessons `no-lower-than-reference` and `closeup-review`.
4. **Later rounds** (not now, one change at a time while the support is re-learned): robustness, the lifted foot in the first stand, the lateral offset.

## Expected after round 4

- In support, only the wrists (and feet) touch the floor; elbows near the reference (about 1.3 rad).
- Segment probe never lost from frame 0 >= 0.6. It may dip while the straight-arm support is learned.
- Landing and hold kept.

Rollback: if `landed_upright` is lost and start-0 never-lost < 0.3, r05 starts from r03 `model_2998` with margin 0.2.
