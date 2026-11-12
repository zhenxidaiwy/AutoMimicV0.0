# Round 4 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** a real cartwheel now: from standing, through a straight-arm inverted support with the head clear of the floor, to an upright landing and a still 7 s hold. Three things remain:
- one foot is lifted in the first stand;
- the final stance is about 0.2-0.3 m beside and a little narrower than the reference;
- robustness is short of the gates.

Inputs:
- `r04_quant.md`;
- all 13 sheets;
- full-resolution close-ups of every frame 0-131 (`videos/cartwheel_2/auto/r04/close/`);
- `floor_contacts.py` / `body_min_z.py` on the eval record (`model_3500`).

## Frame by frame (close-ups 0-131, sheets 120-487)

| frames | robot |
|---|---|
| 0-23 | arms overhead, but the left foot is lifted from frame 1 (left ankle on the floor only at 0 and from 20; reference both feet 0-22); one arm drifts outward at 8-23 |
| 24-47 | lunge sideways with the reference, small lateral lag; arms reach towards the floor |
| 48-71 | straight-arm support: palms on the floor (left 48-73, right 54-77), legs over the top, head clearly up. Floor contacts are only wrists and feet, as in the reference. Minimum heights within 0.04 m of the reference (r03: 0.2 m lower, head and forearms down) |
| 72-95 | lands foot after foot, comes up with the arms forward |
| 96-131 | final wide stance, arms overhead; the stance is about 0.2-0.3 m beside the reference and the trailing leg less extended |
| 132-487 | holds, no visible sway |

## Measured

- Rotation 259.1 deg (reference 255.5). `landed_upright` True, end tilt 14.5 deg.
- Track body error 0.074 m (r03 0.088).
- After the reference: drift 0.016 m, sway 0.012 m.
- Segment probe, never lost from frame 0 / 16 / 30 / 46 / 60 / 81 / 95 / 115: 0.84 / 0.94 / 0.98 / 0.95 / 0.86 / 0.36 / 0.98 / 0.97. The land start (frame 81) is the weak segment (r03 0.39).
- Stop gates that fail:
  - hold: pelvis speed max 0.213 (<= 0.15), sway 0.056 (<= 0.03), drift 0.061 (<= 0.05), tilt error 5.5 deg (<= 5);
  - critic: worst unwaived = `contact:left_foot:stand`, 4.7;
  - robustness: dr 0.76, 20 ms 0.45 (r03 0.65), PD x0.85 0.66 (gates 0.95).
- `term_below_reference` worked as intended: the head / forearm support is gone and nothing else regressed. Rotation, landing, tracking and the segment starts 0-60 all improved.

## Solution for round 5 (three independent targets, one change each)

1. **Lifted foot in the first stand:** switch on the library fix `contact:left_foot:stand` (`dyn_contact`, weight 1.0). It is the worst unwaived critic check.
2. **Hold stillness** (speed / sway / drift / tilt gates): generic `dyn_base_still` in `stand_after` (weight 2, std_v 0.1 m/s, std_w 0.3 rad/s). It was drafted for the backflip r17 and is now used.
3. **Landing robustness:** start-state weight `land` 1 -> 2. The land start is the weakest segment, and the robustness failures end tilted after landing (delay1 end-tilt p95 109 deg).
4. **Warm start** from r04 `model_4497`: the latest checkpoint, the one the segment probe measured. Scores are equal (5.69 vs 5.70 for `model_3500`).

## Expected after round 5

- Left foot on the floor in the first stand (critic `contact:left_foot:stand` < 2).
- Hold pelvis speed max <= 0.15 and sway <= 0.03.
- Segment start 81 never lost > 0.5.
- dr success > 0.8.
- Straight-arm support kept (floor contacts only wrists and feet).

Rollback: if the support returns to head / forearms, or `landed_upright` is lost, go back to r04 `model_4497` with only change 1.
