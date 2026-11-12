# Round 2 (cartwheel_2): LLM analysis (step 2)

Inputs:
- `r02_quant.md` (step 1, now with A3: segment probe);
- the round video `videos/cartwheel_2/auto/r02/r02_model_1000.mp4`;
- all 13 every-step sheets (000-487, reviewed frame by frame);
- the training log `train_cw2auto_r02.log`.

New checks for this analysis:
- `ref_pd_track.py`: can the PD actuators follow the reference arms with the base held?
- `eval_segments.py`: start the policy at reference frames 0 / 16 / 30 / 46 / 60 / 81 / 95 / 115;
- `ref_zmp.py`: ZMP and friction per frame against the contacts present;
- `root_z_compare.py`: root height after each repair step.

## What the frames show

| steps | reference (green) | robot (white) |
|---|---|---|
| 0-7 | stands, arms overhead | tracks |
| 4-23 | arms stay overhead | swings the left arm down and back (shoulder pitch -1.5 -> +1.99 by step 15, +2.68 = limit by step 23), leans to the side |
| 24-40 | lunges, hands go towards the floor | falls on its side and back (earlier than r01, step 48) |
| 40-240 | goes over, lands, stands | lies on the floor; legs and arms move until about step 280 |
| 240-487 (+5 s) | holds the final pose | lies still on its back |

After the reference ends the robot is much quieter than in r01 (action change 0.12 vs 0.88), but it is lying down. `landed_upright` False, end pelvis 0.08 m. The rotation (232.5 deg) again comes from falling and rolling.

## Measured

**Training improved:**
- mean episode length 146 -> 179;
- `ee_body_pos` terminations 15.2 -> 12.5;
- `motion_body_pos` 0.26 -> 0.31, `motion_body_ori` 0.08 -> 0.13;
- `term_flight_spread` / `term_leg_twist` absent (guard passed: reference fires 0 frames).

**Segment probe (A3, model_1499):**
- From frame 60 (inverted on the hands): 75 % finish the cartwheel and stand to the end.
- From frames 95 and 115: 94 % / 98 % never lost.
- From frame 81 (land): 16 %.
- From frame 46 (start of support): lost after 5 steps (frame 51).
- From frames 30 / 16 / 0: lost at frames 39 / 37 / 24.

So the second half is learned. The chain is learned backwards, and the unlearned link is the entry onto the hands (frames 37-51).

**The arms-back behaviour is not physics:** with the base held on the reference, the PD actuators follow the reference arms (left shoulder pitch ends at -1.81 vs reference -1.94). It is a learned strategy: the policy has no working entry onto the hands.

**The entry is where the reference is wrong.**
- *Late hands:* in the r02 reference the planted hands are 6-25 cm above the floor in the first labelled frames.
  - The left palm reaches the floor only at 30 fps frame 36: labelled from 28, about 0.25 s later than the human's.
  - So the reference holds a horizontal torso over one foot for about 0.25 s.
  - The G1 arm is short relative to the body: GMR scales the arms 0.8 and the legs 0.9.
- *Root drop:* `ground_fix --hands` grounds the root per frame on whichever contact is planted. When the foot lifts and the hand takes over, the root drops 7 cm in 2 frames (30 fps 31-33: -21.5 m/s^2, about 2 g down while a foot is on the floor). It jumps again at 43-45 (-18.5 m/s^2). The raw GMR root never exceeds 8.3 m/s^2.
- Both coincide with the frames where the policy loses the reference (50 fps 37-55).
- ZMP: the aggregate is not decisive.
  - Support-phase median ZMP outside the contacts is 0.24 m (r02 reference), against the backflip's takeoff at 0.54 m, which trained fine.
  - It is reported, not used as the reason.

## Solution for round 3

1. **Reference `reachqp_vlm_hold`** (two new generic repairs, then the existing ones):
   1. `ground_fix --qp 30`: root offset by bounded least squares. Planted contacts are pulled to the floor, no point goes below it, and vertical acceleration is penalised. Root |a_z| max: 8.3 raw -> 8.0, against about 21 with the old per-frame offset.
   2. foot lock, then `feet_plant` (stand phases, as in r02).
   3. `arm_reach.py`: arm joints only (7 per arm) put each planted palm on the floor.
      - Mean planted palm height: 7.7 / 8.3 cm -> 1.5 / 1.3 cm. Nothing goes below the floor.
      - Root, legs and waist unchanged. Arm joint change up to 0.86 / 0.97 rad, mostly wrist yaw; elbows 0.4-0.7 rad (straighter arms).
      - QA against GVHMR at t = 0.95-1.55 s: straight arms with palms on the floor, as in the video.
2. **Start-state weights:** lunge 1 -> 3, support 1 -> 2. More starts in the failing entry. The learned second half keeps its share.
3. **Warm start:** r02 `model_1499`. The reward and termination set is unchanged, and it already does the second half. The reference change is local: arms in support and the root height.
4. **Harness:** the segment probe of the last checkpoint runs automatically each round (quant A3).
5. **Library:**
   - generic lessons `segment-probe`, `smooth-root-grounding`;
   - family `hand_support` lesson `arm-reach`.

## Expected after round 3

- Segment probe from frame 46: lost later than frame 51. From frame 30: later than frame 39.
- From frame 60: still >= 0.7 never lost (no regression of the learned half).
- Video: the hands reach the floor, no sideways fall before the support phase.
- `landed_upright` from frame 0: possible but not expected after one round.

Rollback: if the frame-60 start drops below 0.5, go back to the `plant_vlm_hold` reference from r02 `model_1499` and change only the start-state weights.
