# Round 8 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the same clean straight-arm cartwheel and motionless 12 s hold as r07. The only visible difference is that the final stance is again about 0.4 m beside the reference; r07 nearly overlapped it, and the position is not tracked after the event.

Inputs: `r08_quant.md`, all 19 sheets (000-737), close-ups 0-131, `round_look.sh`, `robust_why.py`, the training log.

## Frame by frame

| frames | what the robot does |
|---|---|
| 0-23 | stands on both feet with the arms overhead, overlapping the reference |
| 24-47 | lunges and brings the torso horizontal |
| 45-77 | straight-arm support with the palms down and the head clear; only wrists and feet touch, plus the right knee at 72 (+0.6 cm) |
| 78-95 | lands right foot first, then left |
| 96-131 | upright wide stance, arms overhead, about 0.4 m beside the reference |
| 132-737 | no visible motion |

## Measured, r07 -> r08

Nominal run:
- Rotation: 261.0 -> 264.3 deg.
- Tracking error: 0.040 m (unchanged).
- Hold: speed, sway and drift all 0.002 m or less.
- Segment probe: 1.0 at every start.

Robustness (success rate):

| scenario | r07 | r08 |
|---|---|---|
| dr | 0.85 | 0.87 |
| 20 ms latency | 0.64 | 0.66 |
| kp x0.85 | 0.79 | 0.83 |

- `robust_why`: every failure is still drift.
  - Post-drift p95 is 0.41 / 0.61 / 0.51 m (dr / 20 ms / kp), down from 0.43 / 0.68 / 0.53.
  - Under 20 ms latency some runs also under-rotate: rotation p5 is 227 deg, the limit is 230.
- `dyn_hold_spot` was trained but is weak. It contributes 0.38 per episode at weight 2, against 0.22 for `base_still` and roughly 1-2 for the tracking terms.
  - It moved drift only a little.
- The weakest scenario is latency. The training randomises the delay uniformly over 0-25 ms, so 20 ms sits at the tail of what the policy has seen.
  - The backflip reached 99 % at 20 ms with the same setup. The cartwheel's long, slow support phase is more sensitive.

## Solution for round 9 (two changes, each with its own target)

1. **Latency in training: `delay_ms` 25 -> 40.** A 20 ms delay is then in the middle of the trained range, not at its tail (generic lesson `control-latency`).
2. **Hold on the spot harder: `dyn_hold_spot` weight 2 -> 4, std 0.15 -> 0.10 m.** The drift limit is 0.3 m. At 0.3 m the old reward still paid exp(-2) = 0.14; the new one pays 0.05 with a steeper gradient near the spot.
3. Warm start from r08 `model_10493`.

## Expected after round 9

- 20 ms latency success > 0.8, rotation p5 >= 230 deg.
- dr and kp x0.85 success > 0.9, post-drift p95 < 0.3 m.
- Nominal run unchanged.

**Rollback:** if the nominal run loses the landing or the hold (any hold gate fails), r10 starts again from r08 `model_10493` with only change 2.
