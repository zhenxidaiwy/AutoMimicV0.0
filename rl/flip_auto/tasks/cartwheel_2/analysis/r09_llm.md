# Round 9 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** this run is the same clean straight-arm cartwheel and still hold as r08. It is now robust to pushes and +20 ms latency for almost every run. What it lost: the support is a little less tidy (feet land slightly off the reference, wrists jitter on landing), and the final stance is more upright than the reference's lean.

Inputs: `r09_quant.md` (A2 now with v1 and v2), all 19 sheets, close-ups 0-131, `round_look.sh`.

## Frame by frame

| frames | what the robot does |
|---|---|
| 0-23 | stands on both feet, arms overhead |
| 24-47 | lunges, torso goes horizontal |
| 48-74 | straight-arm support, palms down, head clear; contacts only wrists and feet |
| 72-95 | lands right foot, then left |
| 96-131 | upright wide stance, about 0.3 m beside the reference |
| 132-737 | no visible motion |

## Measured, r08 -> r09

Robustness success, v2 (drift < 0.5 m under pushes) and v1 (drift < 0.3 m):

| scenario | r08 v1 | r09 v1 | r09 v2 |
|---|---|---|---|
| dr | 0.87 | 0.957 | 0.992 |
| 20 ms latency | 0.66 | 0.762 | 0.941 |
| kp x0.85 | 0.83 | 0.938 | 0.996 |
| 40 ms latency | 0.20 | 0.305 | 0.473 |

Under 20 ms latency the 5th-percentile rotation rose from 227 to 249 deg, so under-rotation is gone.

What it cost:
- Tracking error: 0.040 -> 0.062 m.
- Hold tilt error: 2.5 -> 6.1 deg; the robot stands more upright than the reference.
- Critic, worst unwaived check: `jitter:wrist_roll:land` at 4.98 (left wrist roll, acceleration RMS 85 vs 1 in the reference). The wrist shakes while the hand leaves the floor.

These follow from training against 0-40 ms delays: the policy trades precision for robustness.

Stop gates still failing:
- `robust_latency_20ms`: 0.941 v2, gate 0.95.
- `hold_posture_tilt`: 6.1, gate 5.
- `critic_clean`: 4.98, gate 3.

Every other gate passes.

## Solution for round 10 (finishing round)

1. **Wrist jitter on landing:** switch on the library fix `jitter:wrist_roll:land` (`dyn_quiet`, weight 1).
2. **Hold posture:** add a generic `dyn_joint` on the waist and legs in `stand_after`, weight 1, std 0.15. The tilt error comes from the hip / waist angle, and every other hold gate already passes.
3. **Keep** delay 40 ms, `hold_spot` and everything else; warm start from r09 `model_11992`.

## Expected after round 10

- 20 ms latency v2 >= 0.95.
- Hold tilt <= 5 deg.
- Critic worst check <= 3.

If all gates pass, the next step is the sim2sim exam.

**Rollback:** if robustness drops back (dr v2 < 0.95), run r11 from r09 `model_11992` with only fix 1.
