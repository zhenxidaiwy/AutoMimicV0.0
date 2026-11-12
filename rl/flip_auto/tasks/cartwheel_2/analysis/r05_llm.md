# Round 5 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the same clean straight-arm cartwheel as r04, now steadier: lands upright and stands motionless for 7 s. But it still lifts its left foot about 10 cm for the first 0.3 s of the opening stand, and it holds the final stance about 0.3 m beside the reference.

Inputs:
- `r05_quant.md`;
- all 13 sheets (000-487);
- full-resolution close-ups 0-131 (`videos/cartwheel_2/auto/r05/close/`);
- `floor_contacts.py`;
- `ankle_z.py` (new: ankle height and knee, robot vs reference).

## Frame by frame

| frames | robot |
|---|---|
| 0-15 | arms overhead; the left knee bends 0.19 -> 0.74 rad and the left ankle rises to 0.138 m at steps 8-9 (reference: 0.035 m, knee 0.10, both feet down). Back on the floor at step 16 |
| 16-47 | lunge, lean, hands towards the floor, legs up |
| 48-75 | straight-arm support, palms down (left 51-75, right 55-78), head clear of the floor; contacts are only wrists and feet |
| 76-95 | lands foot after foot, comes up with the arms forward |
| 96-131 | final wide stance, arms overhead, about 0.3 m beside the reference (allowed: after the event only height is tracked, lesson `walk-to-reference`) |
| 132-487 | still; no visible sway in any sheet |

## Measured (r04 -> r05)

- Track body error: 0.074 -> 0.058 m.
- After the reference: drift 0.016 -> 0.002 m, sway 0.012 -> 0.001 m.
- Hold: pelvis speed max 0.213 -> 0.085 (gate passes), sway 0.056 -> 0.042 (gate 0.03), drift 0.061 -> 0.051 (gate 0.05), tilt error 5.5 -> 4.0 deg (passes).
- Robustness:

  | scenario | r04 | r05 |
  |---|---|---|
  | nominal | 0.99 | 1.00 |
  | training randomisation | 0.76 | 0.78 |
  | +20 ms delay | 0.45 | 0.73 |
  | PD x0.85 | 0.66 | 0.75 |

  The gates are 0.95.
- Segment probe, never lost from frame 0 / 81: 0.84 -> 0.94 / 0.36 -> 0.47.
- `dyn_contact` for the left foot (weight 1) did nothing: severity 4.7 -> 4.3, still 13 of 16 steps off the floor. The policy takes a deliberate small step, not a stumble. The knee bends at once from step 1, and the foot is put down again exactly when the lunge starts.

## Solution for round 6

1. **New generic termination `term_foot_lifted`** (`rl/mimic_generic.py`):
   - Applies in the `stand` phases.
   - Terminates if a foot the reference has planted (its ankle below 6 cm) is more than 5 cm higher than the reference's ankle.
   - The reference passes by construction.
   - This replaces the reward that did not work (same lesson as `no-lower-than-reference`: a hard constraint where a soft reward is ignored).
2. **`dyn_base_still` weight 2 -> 3:** sway 0.042 and drift 0.051 are just above the gates, and speed already passes.
3. **Start-state weight `land` 2 -> 3:** the land start improved with the extra weight (0.36 -> 0.47) and is still the weakest segment.
4. **Warm start** from r05 `model_5996`, the checkpoint the segment probe measured.
5. The library fix `contact:left_foot:stand` stays on: it is harmless and supports the termination.

## Expected after round 6

- Left ankle within 5 cm of the reference in the first stand (critic `contact:left_foot:stand` < 2).
- Hold sway <= 0.03 and drift <= 0.05.
- Segment start 81 > 0.5.
- Support and landing kept.

Rollback: if segment start 0 drops below 0.7 (the termination too hard at the start), r07 from r05 `model_5996` with `max_lift` 0.08.
