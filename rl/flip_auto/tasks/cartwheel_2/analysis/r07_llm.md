# Round 7 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the best round so far. It is a clean straight-arm cartwheel from a two-footed stand. The robot lands and then stands completely still for the whole 12 s run, and its final stance now almost overlaps the reference. Only robustness under pushes and latency is still below the gates.

Inputs:
- `r07_quant.md`;
- all 19 sheets (000-737; the run is longer because the reference now holds 7.5 s);
- close-ups 0-131;
- `round_look.sh`;
- `robust_why.py`.

## Frame by frame

| frames | robot |
|---|---|
| 0-23 | both feet down, arms overhead, overlaps the reference |
| 24-47 | lunge, torso to horizontal, legs up |
| 48-77 | straight-arm support, palms down, head clear (contacts: wrists and feet only) |
| 78-95 | lands right then left foot, comes up |
| 96-131 | wide final stance, arms overhead, close to the reference (r06: about 0.4 m beside it) |
| 132-737 | no visible motion in any sheet |

## Measured (r06 -> r07)

| metric | r06 | r07 |
|---|---|---|
| track body error (m) | 0.064 | 0.040 |
| rotation (deg) | 252.5 | 261.0 (reference 255.5) |
| hold tilt error (deg) | 9.4 | 2.2 |
| hold sway / drift / speed | 0.025 / 0.027 / 0.106 | 0.000 / 0.000 / 0.000 |
| segment probe, all 8 starts | | 1.0 never lost |

- **Stop gates:** every hold / post / family gate passes. Still failing:
  - `critic_clean`: 3.23 vs 3.0, worst `body:ankle_roll:land`;
  - robustness:

    | scenario | r06 | r07 |
    |---|---|---|
    | training randomisation | 0.81 | 0.85 |
    | +20 ms delay | 0.65 | 0.64 |
    | PD x0.85 | 0.73 | 0.79 |

    The gate is 0.95.
- **`robust_why`:** all failures are drift, with post drift p95 of 0.43 / 0.68 / 0.53 m against the 0.3 m limit. Tilt, height and rotation pass.
- **Why it drifts:** with pushes on, the robot steps away and stays there. After the event the global position is free, and `dyn_base_still` only penalises speed, so nothing brings it back.

## Solution for round 8

1. **New generic template `dyn_hold_spot`** in `stand_after` (weight 2, std 0.15 m): rewards the pelvis staying at its own first hold position, recorded per episode. This targets the drift that remains after a push.
2. **Everything else unchanged.** Warm start from r07 `model_8994`.

## Expected after round 8

- Robustness drift p95 < 0.3 m.
- dr / 20 ms / PD x0.85 success > 0.9.
- Nominal hold stays still; cartwheel kept.

Rollback: if the nominal run starts to shuffle (hold speed max > 0.15) or the cartwheel regresses, r09 from r07 `model_8994` with weight 1.
