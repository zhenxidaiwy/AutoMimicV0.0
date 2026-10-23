# Round 8 - LLM analysis (step 2: causes and priorities; step 3 = decisions/r09.json)

Inputs: analysis/r08_quant.md (step 1), every-step HD sheets 000-187 (all five reviewed), joint tables robot vs
reference (joint_table.py), training log r08.

Process note: a first r09 was launched before this analysis was complete (sheets 000-079 unreviewed, no written
quantitative report). The user stopped the shortcut; that run was killed after a few minutes
(`*_flipauto_r09_aborted_skipped_review`) and the library restored to the end of r08. The harness now refuses a
decision without this file, the quantitative report and all sheets reviewed.

## 0. What r08 actually trained (audit, section F)

- library fixes: **0 active in training** (the r08 harness process predates `--dyn-rewards`); the 12 fixes that the
  rules had switched on in library.json were never trained. Earlier claim "the fixes ran and failed" was wrong.
- `flip_stand_quiet` missing, `motion_global_root_ori` still global (not `flip_root_ori`), no waist-yaw termination.
- So r08 tested only the rule-adjusted weights (stay_down 10, tuck 9, legs 6, tracking x2.25 / std x0.72).

## 1. What the sheets show (all 188 steps)

| steps | phase | observation |
|---|---|---|
| 0-63 | stand, arms up | robot on the green reference, arm raise on time |
| 64-90 | crouch | close; arms swing back (waist pitch -0.24 vs +0.52 at step 79, sev 2.0) |
| 91-100 | take-off | hips extend to +0.1 rad, no early take-off (r07 fell early) |
| 101-108 | early flight | knees fold to 2.4-2.8 rad (ref 0.5-1.4) while hips stay at -0.3..-0.85 (ref -1.44..-1.57): a knee tuck, hip tuck ~9 steps late |
| 102-124 | flight / land | arms thrown back and asymmetric: L shoulder pitch +1.14 vs ref -1.23, shoulder yaw L/R differ 138 deg (ref 4) |
| 120-128 | land | both feet down together, upright |
| 130-187 | stand | waist turns steadily to +1.86 rad (107 deg); arms counter-swing (L pitch -0.7, R +0.6 vs -0.1); feet lift 18 (L) / 10 (R) of 58 steps; ankle acceleration ~100 rad/s^2 = trembling |

## 2. Causes (physics / training)

1. **Waist twist after landing**: the global orientation tracking term pulls the pelvis heading to the reference's;
   once the feet are planted, the cheapest way is the waist yaw. With no quiet / waist term, the arms swing to
   balance the twist. The fixes for this exist in code (flip_root_ori, stand_still on all joints, stand_quiet, waist
   termination) but have never been trained.
2. **Off-plane rotation (plane deviation 11.5 -> 18.5 deg)**: arms asymmetric in the air carry angular momentum about
   the vertical / forward axes; an asymmetric arm pose during take-off injects twist. Nothing in r08's rewards looks
   at the arms in the air (tracking is weak there and the arm templates were not trained).
3. **Rotation 373 -> 344 deg, at the reference landing 285 vs 323 deg**: inertia stays large early in flight because
   the hips tuck ~9 steps late; the policy folds the knees instead (cheaper with the tuck reward's knee tolerance and
   the hip termination at 0.0 rad). Landing comes 22 steps after the reference.
4. **Template fixes as defined would not help**: at r08's errors exp(-err/std) is 1e-5..1e-2 for most active fixes
   (section C), i.e. no gradient; std must match the current error.

## 3. Priorities (severity x consequence for the real robot)

| P | problem | measured | why this rank |
|---|---|---|---|
| P1 | stand after landing: waist twist, arm counter-swing, trembling, feet lifting | waist 1.86 rad, arm err 29 deg, action change 0.30, ankle acc ~100 rad/s^2 | decides whether the skill is usable / safe on the real G1 (heating, falls); fixes exist but never trained |
| P2 | flight arms asymmetric, thrown back | shoulder-yaw asym 138 deg, sev 13.4 | physical cause of the off-plane twist; affects landing direction |
| P3 | hip tuck late, knees over-folded | hip -0.6 vs -1.53 at step 105, knee overfold 2.06 rad, rotation -29 deg | rotation margin; but the flip still completes and lands |
| P4 | weight balance | stay_down 10 (x2 = 20) vs spin 3 (x2 = 6) | early fall is solved; keep margin but reduce dominance |
| - | wrists in stand (sev 2-3.6), crouch waist pitch (sev 2) | | cosmetic / no effect on the flip; monitor only |

## 4. Solution (-> decisions/r09.json)

- P1: the r07 stand code runs for the first time (module default; verify in the r09 log: flip_root_ori replaced,
  flip_stand_quiet present, waist termination) + arm pose term for settle / stand_after, std 0.5 (= current mean
  error 29 deg), weight 2; stand_still and stand_quiet weights 2 -> 3.
- P2: arm pose term over take-off / flight / land, std 0.8 (errors 1-2 rad -> signal 0.1-0.3), weight 2;
  shoulder-yaw symmetry fixes kept with std 0.8.
- P3: hip-pitch term in flight, std 0.6, weight 3; knee template std 0.8.
- P4: stay_down 10 -> 5. Tracking curriculum unchanged this round (one fidelity change at a time).
- Library (decider, not rules): of the 12 rule-enabled fixes keep the ones that do not overlap the new terms, all
  with std matched to the error; switch off the ones the arm pose terms cover.
- Expected (r09): waist_yaw stand < 0.4 rad, stand action change < 0.2, shoulder-yaw asym in flight < 60 deg,
  hip pitch at step 105 <= -1.0, rotation >= 340 deg, plane deviation < 15 deg.
- Rollback: no upright landing or rotation < 300 deg -> r10 starts again from r08 model_5500 with the arm terms halved.
