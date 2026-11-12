# Round 6 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** both feet now stay on the floor in the opening stand. The cartwheel itself (lunge, straight-arm support, landing) is as clean as r05, and the robot holds the final stance motionless for 7 s. Its torso is more upright than the reference's slight lean, and it stands about 0.4 m beside the reference.

Inputs:
- `r06_quant.md`;
- all 13 sheets;
- close-ups 0-131;
- `round_look.sh` (contacts, ankle heights, labelled contacts);
- `robust_why.py` (new: which success condition fails);
- a re-run of the segment probe.

## Frame by frame

| frames | robot |
|---|---|
| 0-23 | both feet down (left ankle 0.035-0.047 m vs reference 0.035; r05 rose to 0.138), arms overhead |
| 24-47 | lunge, torso to horizontal, legs up |
| 48-75 | straight-arm support, palms down, head clear; floor contacts: wrists and feet (plus 1 step of the right knee at 73, +0.8 cm) |
| 76-95 | lands right foot first, then left |
| 96-131 | final wide stance, more upright than the reference (hold tilt error 9.4 deg, r05 4.0) |
| 132-487 | no visible sway |

## Measured

- **First stand fixed:** `contact:left_foot:stand` no longer fails; `term_foot_lifted` worked.
- **Hold:** sway 0.042 -> 0.025 and drift 0.051 -> 0.027, both now pass. Pelvis speed max 0.106 passes. Tilt error 9.4 deg fails (gate 5): the robot stands more upright than the leaning reference.
- **Robustness:** nominal 1.0, dr 0.81, 20 ms 0.65, PD x0.85 0.73.
  - `robust_why.py`: in every perturbed scenario the failures are drift. Post drift p95 is 0.48 / 0.81 / 0.67 m (limit 0.3), while rotation, tilt (< 25 deg) and pelvis height pass.
  - The robot does not fall; it steps away under the pushes in the 5 s past the reference.
  - That window was never trained: an episode resamples the reference at its end, and only 2.5 s of hold exist in the reference.

**Two measurement errors found and fixed (generic):**
1. **Segment probe:**
   - After the main event the heading is free (`flip_root_ori`), but the probe counted the full orientation error, so a standing robot with a different heading counted as "lost".
   - With tilt only after the event, every start (0 / 46 / 81 / 95) is 1.0 never lost. The r04-r06 "weak land segment" (0.20-0.47) was this artifact.
   - The `prior.land` increases of r05 / r06 were based on it.
2. **Contact check:**
   - The critic required both feet down in every land / settle frame. A cartwheel lands one foot after the other, so it flagged the left foot while the reference's own left foot was still 8-60 cm up.
   - It now counts only steps where the reference has that foot down. The remaining real one: right foot in `land`, 9 of 14 steps (severity 3.0, a short hop on landing).

## Solution for round 7

1. **Train the judged window:** new reference `reachqp_vlm_hold8` (the same motion with a 7.5 s held final pose, 490 frames = 9.8 s, within the 10 s episode). The pushes and latency of training then also act during a long hold.
2. **`prior.land` back to 1:** its reason was the probe artifact.
3. **Keep** `term_below_reference`, `term_foot_lifted`, `dyn_base_still` (w 3) and the contact fix.
4. **Warm start** from r06 `model_7495`.
5. **Library lessons:** `train-the-judged-window`, `probe-heading-after-event`, `contact-check-ref-relative`.

Not changed: the hold tilt error (9.4 deg). The robot is more upright than the reference, which is not worse posture. Re-measure after the longer hold before acting.

## Expected after round 7

- Robustness drift p95 < 0.3 m: dr, 20 ms and PD x0.85 success > 0.9.
- Hold sway / drift stay within the gates.
- Cartwheel and first stand kept.

Rollback: if the cartwheel regresses (rotation < 230 or support contacts beyond the wrists), r08 from r06 `model_7495` on the 2.5 s hold reference.
