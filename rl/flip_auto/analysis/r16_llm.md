# Round 16 - LLM analysis (step 2)

Inputs: analysis/r16_quant.md (incl. A2 robustness and S stop criteria, first round evaluated with the +5 s
recording), all 11 every-step sheets 000-437 (188 reference steps + 250 post-reference steps), sway_joints.py on the
record (steps 188-438), human input of 2026-10-23 on the r15 +5 s video.

## 1. What r16 changed and whether it worked
r16 = r15 + the delay-buffer fix (no 0-rad targets after a reset), nothing else.
- quiet after landing recovered: stand_action_change 0.185 -> 0.072, stand_pelvis_speed 0.27 -> 0.117 m/s,
  stand_torso_angvel 0.69 -> 0.41 rad/s, arm velocity 1.09 -> 0.47 rad/s. The r15 regression was the bug.
- flight best so far on plane deviation: 5.8 deg max (r15 11.2); rotation 363 deg; landing on time (+2 steps).
- tracking converged: body error 0.0699 m (r15 0.0698) -> convergence gate passes.

## 2. Sheets (every step)
- 000-100 stand / arm raise / crouch / take-off: on the ghost.
- 100-120 flight: tight tuck, legs together, in plane.
- 120-130 land: both feet, arms forward, upright.
- 130-188 settle/stand: upright, ~one body width left-front of the ghost (landing offset, not corrected), arms down.
- 188-437 the 5 s past the reference: stays up the whole time, feet never lift (0 steps), no fall; slow forward
  creep and small shifts of knees / hands; it never re-aligns with the ghost. Matches the human input on r15
  ("站住之后前后移动，各个部分稍微有点晃").

## 3. Measured hold behaviour
| | value | gate |
|---|---|---|
| hold window available in the training reference | 0.66 s | >= 2 s FAIL (reference too short) |
| pelvis speed max (last 0.66 s) | 0.26 m/s | <= 0.15 FAIL |
| torso angular velocity RMS | 0.56 rad/s | <= 0.2 FAIL |
| joint pose error vs final pose | 0.155 rad | <= 0.15 FAIL (marginal) |
| 5 s past the reference: drift / sway / tilt error | 0.114 m / 0.069 m / 3.4 deg | pass / - / pass |
| fore/aft vs lateral (post window) | range 0.125 m (net +0.095 fore) / 0.094 m (net -0.063) | slow creep, not oscillation |
| moving joints in the post window (velocity RMS, rad/s) | wrist roll L/R 0.71/0.70, L ankle pitch 0.68, hip yaw R/L 0.64/0.62, wrist pitch 0.53, knee 0.42 | |

Robustness with the new criterion (flip + stay up and drift < 0.3 m over 5 s past the reference):
nominal 95.7 %, dr 42 %, delay 20 ms 27 %, kp x0.85 35 %, delay 40 ms 0 %. r15 under the same criterion: nominal
96.9 %, delay 20 ms 25 % (32 envs) - so this is not a regression of r16; the old end-of-clip criterion hid it. Falls
are rare (0-2 %); the failures are drift > 0.3 m during the hold.

## 4. Causes
1. **The final pose was never trained beyond 0.7 s.** The reference stops 0.7 s after the settle phase; the policy
   only ever saw that short tail, so holding longer is extrapolation - under any perturbation (DR, latency, PD
   error) it creeps away. This is the main cause of the robustness failures.
2. **Nothing pays for staying in place.** After landing the anchor position term tracks height only (by design,
   r6), and flip_stand_still uses a pelvis-velocity scale of 0.6 m/s: at the measured 0.1-0.26 m/s it is ~0.7-0.85
   of its maximum, i.e. almost no gradient against a slow creep. jitter:all:stand_after (dyn_quiet, std 1.0 rad/s)
   is likewise flat at the measured 0.4-0.7 rad/s joint speeds.
3. Small "every part sways": wrists / ankle pitch / hip yaw / knee move at 0.4-0.7 rad/s RMS while the reference is
   static - consistent with 2 (no signal) rather than a balance problem (feet never lift, tilt error 2-3 deg).

## 5. Priorities
| P | problem | why |
|---|---|---|
| P1 | train the held final pose (>= 2.5 s) | precondition of the user's 2 s rule and of every hold / robustness gate |
| P2 | pay for not moving in the final pose: base velocity + torso rate, joint velocities with std of the measured error | the creep and the small sway; robustness under DR / latency / PD |
| P3 | keep the flip (rotation, plane, tracking) | best flight so far; no change to flight terms |
| - | wrists: still waived as GVHMR artefacts for tracking, but their VELOCITY in the hold is covered by P2 | |

## 6. Decision -> decisions/r17.json (DRAFT, not launched: user stopped for the weekend)
reference -> ballistic_hold (280 frames, 2.5 s held final pose); new generic template dyn_base_still on stand_after
(std_v 0.1 m/s, std_w 0.3 rad/s, weight 4); jitter:all:stand_after std 1.0 -> 0.3; start from r16 model_14998.
Expect: hold gates pass (speed <= 0.15, sway <= 0.03, torso <= 0.2, pose <= 0.15), robust dr / delay 20 ms / kp
>= 0.8 with the new criterion, rotation >= 350, plane <= 10. Rollback: rotation < 340 or flight plane > 12 deg ->
r18 from r16 model_14998 with the hold terms halved.
