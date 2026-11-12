# Round 10 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the nominal playback is still a clean straight-arm cartwheel that lands and holds still, but it looks no better than r09. The final stance is still more upright than the reference's lean, and under perturbations the policy got clearly worse.

Inputs: `r10_quant.md` (A2 v1/v2, A3, S), close-ups 0-131 (every frame), all 19 sheets 000-737, `round_look.sh`.

## Frame by frame (model_13491)

| frames | what the robot does |
|---|---|
| 0-23 | stands, arms overhead; left knee bent 0.27 -> 0.94 rad while the reference keeps it at 0.10 (left foot stays down, ankle z 0.04 m) |
| 24-47 | lunge, torso goes horizontal |
| 48-71 | straight-arm support, palms down, head clear; only wrists and feet touch the floor (floor_contacts) |
| 72-95 | lands right foot then left; the robot is about 0.3 m beside the reference, with the right foot off the floor for 8 of the 14 landing steps the reference has it down |
| 96-131 | upright wide stance, arms overhead, more upright than the reference |
| 132-737 | no visible motion (sheet 440-479: identical frames) |

## Measured, r09 -> r10

| metric | r09 | r10 |
|---|---|---|
| robust dr v2 / v1 | 0.992 / 0.957 | 0.879 / 0.82 |
| robust 20 ms v2 / v1 | 0.941 / 0.762 | 0.707 / 0.59 |
| robust kp x0.85 v2 / v1 | 0.996 / 0.938 | 0.871 / 0.809 |
| robust nominal | - | 0.965 |
| hold tilt error (deg, gate 5) | 6.1 | 6.7 |
| hold pose error (rad) | 0.072 | 0.054 |
| tracking body error (m) | 0.062 | 0.052 |
| critic worst unwaived | 4.98 (wrist roll, land) | 3.45 (ankle_roll body position, land) |

The perturbed runs fail mostly on end tilt and drift (p50 end tilt 19-22 deg, drift p95 0.37-0.53 m), not on falling (fell <= 1.2 % except 40 ms).

## Diagnosis

- The new `agent_r10_hold_posture` (`dyn_joint` on waist and legs, std 0.15) lowered the joint-pose error (0.072 -> 0.054) but the tilt error rose (6.1 -> 6.7). So the tilt gap is not a joint-angle gap: the joints already match, and the whole body is rotated more upright. A joint term cannot fix that.
- The same term pins the legs to the reference stance in `stand_after`. That is exactly where the robot has to step or shift to recover from pushes and delay, and all three robustness scenarios fell by 0.11-0.23 at once. The wrist fix is the only other change and acts only in `land`.
- The wrist fix worked: `jitter:wrist_roll:land` dropped from 4.98 to 2.3.

## Decision for round 11: rollback (r10 rule `dr v2 < 0.95` triggered)

- init r09 `model_11992`. Keep the wrist fix `jitter:wrist_roll:land`; drop `agent_r10_hold_posture`. Everything else as in r09.
- Hold tilt stays open. A joint-space term is the wrong tool, as this round shows. If it is still the only failing gate after r11, the next step is a measurement of where the tilt comes from (pelvis vs torso, which axis), not another posture reward.

## Expected after round 11

- Robustness back to r09 level (dr / kp v2 >= 0.95, 20 ms >= 0.94).
- Critic worst unwaived <= 3 (wrist fix kept).
- Hold tilt about 6 deg (unchanged).
