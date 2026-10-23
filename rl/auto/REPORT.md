# Get-up self-iteration report (rl/auto/harness.py)

Targets: success >= 0.97; time-to-stand median 2.0-3.5 s; every pose >= 1.8 s; feet distance while rising <= 0.45 m; squat match >= 0.5; peak joint speed <= 10 rad/s; torso tilt <= 3 deg; standing template >= 0.9; keeps stance from a standing start (template >= 0.9)

## Round 0  (2026-10-20 23:26)  score 8.31  **best so far**

- run `2026-10-20_22-43-59_auto_r00`, checkpoint `model_22597.pt`; video `videos/getup/auto_r00.mp4`
- success 100%, time-to-stand median 2.15 s; per pose: supine 2.18 s (100%), face-down 2.12 s (100%), left side 2.21 s (100%), right side 2.04 s (100%)
- feet distance while rising 0.46 m, squat match 0.01, peak joint speed 7.8 rad/s (accel 292), peak pelvis |vz| 0.60 m/s, max pelvis z 0.77 m
- stance: torso tilt 1.0 deg, pelvis tilt 1.1 deg, template 0.96; from a standing start: template 0.96, still standing 100%
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, X feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, OK standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -80.0, "feet_max_dist": 0.35, "w_squat": 4.0, "squat_std": 0.08, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.0, "stand_prob": 0.4, "squat_prob": 0.15}`
- next round changes:
  - w_feet_spread -80.0 -> -120.0 (feet 0.46 m apart while rising)
  - w_squat 4.0 -> 6.0 (squat match 0.01)
  - squat_prob 0.15 -> 0.2 (squat match 0.01)

## Round 1  (2026-10-21 00:11)  score 8.50  **best so far**

- run `2026-10-20_23-27-29_auto_r01`, checkpoint `model_24096.pt`; video `videos/getup/auto_r01.mp4`
- success 100%, time-to-stand median 2.06 s; per pose: supine 2.06 s (100%), face-down 2.10 s (100%), left side 2.11 s (100%), right side 1.92 s (100%)
- feet distance while rising 0.41 m, squat match 0.05, peak joint speed 8.4 rad/s (accel 302), peak pelvis |vz| 0.58 m/s, max pelvis z 0.77 m
- stance: torso tilt 0.9 deg, pelvis tilt 0.7 deg, template 0.98; from a standing start: template 0.98, still standing 100%
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, OK standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 6.0, "squat_std": 0.12, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.0, "stand_prob": 0.4, "squat_prob": 0.2}`
- next round changes:
  - w_squat 6.0 -> 9.0 (squat match 0.05)
  - squat_prob 0.2 -> 0.25 (squat match 0.05)
  - squat_std 0.12 -> 0.16 (squat match 0.05: widen the kernel so the reward has a gradient)

## Harness restarted (2026-10-21 00:13): new targets (no stomping / balance stepping), all rounds re-measured; best = round 0 (score 6.12)

- next round changes:
  - w_feet_spread -80.0 -> -120.0 (feet 0.46 m apart while rising)
  - w_squat 4.0 -> 6.0 (squat match 0.01)
  - squat_prob 0.15 -> 0.2 (squat match 0.01)
  - squat_std 0.08 -> 0.12 (squat match 0.01: widen the kernel so the reward has a gradient)
  - w_feet_move_stand -20.0 -> -30.0 (balance stepping: feet travel 0.16 m after standing)
  - w_feet_move_rise -1.0 -> -1.5 (stomping: 6.0 touchdowns while rising)

## Override before round 2: continue from `2026-10-20_21-37-02_getup_v7f_n2048/model_19500.pt` (user pick: v7f model_19500 looks best); earlier rounds no longer count as best

## Round 2  (2026-10-21 00:59)  score 8.23  **best so far**

- run `2026-10-21_00-13-24_auto_r02`, checkpoint `model_20999.pt`; video `videos/getup/auto_r02.mp4`
- success 99%, time-to-stand median 2.48 s; per pose: supine 2.48 s (100%), face-down 2.52 s (96%), left side 2.56 s (100%), right side 2.24 s (100%)
- feet distance while rising 0.43 m, squat match 0.20, peak joint speed 8.6 rad/s (accel 291), peak pelvis |vz| 0.52 m/s, max pelvis z 0.76 m
- stance: torso tilt 2.6 deg, pelvis tilt 3.0 deg, template 0.78; from a standing start: template 0.88, still standing 100%
- feet: 3.0 touchdowns while rising, 0.0 after standing, foot travel after standing 0.04 m, peak foot force 374 N
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, X standing template >= 0.9, X keeps stance from a standing start (template >= 0.9), OK no balance stepping after standing (foot travel <= 0.05 m), OK no stomping while rising (touchdowns <= 4), OK no hard foot impacts (peak force <= 500 N)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 6.0, "squat_std": 0.12, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.0, "stand_prob": 0.4, "squat_prob": 0.2, "w_feet_move_stand": -30.0, "w_feet_move_rise": -1.5, "w_foot_impact": -2.0}`
- next round changes:
  - w_squat 6.0 -> 9.0 (squat match 0.20)
  - squat_prob 0.2 -> 0.25 (squat match 0.20)
  - w_stand_template 6.0 -> 7.8 (stance: tilt 2.6 deg, template 0.78, from standing 0.88)

## Round 3  (2026-10-21 12:52)  score 0.60

- run `2026-10-21_12-08-06_auto_r03`, checkpoint `model_22498.pt`; video `videos/getup/auto_r03.mp4`
- success 23%, time-to-stand median 2.56 s; per pose: supine nan s (0%), face-down nan s (0%), left side 2.56 s (100%), right side nan s (0%)
- feet distance while rising 0.00 m, squat match 0.00, peak joint speed 7.4 rad/s (accel 248), peak pelvis |vz| 0.33 m/s, max pelvis z 0.76 m
- stance: torso tilt 1.6 deg, pelvis tilt 1.4 deg, template 0.94; from a standing start: template 0.94, still standing 100%
- feet: 0.0 touchdowns while rising, 0.0 after standing, foot travel after standing 0.00 m, peak foot force 215 N
- targets: X success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, OK standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9), OK no balance stepping after standing (foot travel <= 0.05 m), OK no stomping while rising (touchdowns <= 4), OK no hard foot impacts (peak force <= 500 N)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 9.0, "squat_std": 0.12, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 7.8, "stand_prob": 0.4, "squat_prob": 0.25, "w_feet_move_stand": -30.0, "w_feet_move_rise": -1.5, "w_foot_impact": -2.0}`
- next round changes:
  - w_feet_spread -120.0 -> -84.0 (success 0.23 < 0.95: relax the constraints)
  - w_squat 9.0 -> 7.2 (success 0.23 < 0.95: relax the constraints)
  - w_rise_schedule -1000.0 -> -800.0 (success 0.23 < 0.95: relax the constraints)
  - w_joint_speed_cap -0.2 -> -0.16 (success 0.23 < 0.95: relax the constraints)

## Fix before round 4 (2026-10-21 13:10, manual): round 3 collapsed (success 23%)

- Symptom: from supine / face-down / right side the robots sat at pelvis 0.17 m with the legs wide open for the whole
  episode (left side still stood up). The collapse showed within the first 100 iterations of round 3.
- Cause 1, reward cliff: feet_spread switched on at once when the pelvis passed 0.2 m (w -120): rising from a
  wide-legged sit cost ~24/s immediately, so sitting just below 0.2 m became a local optimum.
  Fix: the gate ramps from 0 at 0.2 m to 1 at 0.45 m (knob feet_spread_ramp).
- Cause 2: feet_move_stand also fired while catching the random training pushes (~10.6/s in round 2, half of the
  standing reward), making standing less attractive. Fix: only while the pelvis moves < 0.15 m/s horizontally
  (knob feet_still_body_speed) - stepping without a reason is still penalised.
- New term floor_stall (w -5): pelvis still below 0.4 m 0.5 s after the rising schedule has ended.
- Round 4 restarts from round 2 (model_20999) with the half-step knobs.

## Round 4  (2026-10-21 13:40)  score 7.55

- run `2026-10-21_12-55-41_auto_r04`, checkpoint `model_22000.pt`; video `videos/getup/auto_r04.mp4`
- success 100%, time-to-stand median 2.16 s; per pose: supine 2.10 s (100%), face-down 2.18 s (100%), left side 2.18 s (100%), right side 1.94 s (100%)
- feet distance while rising 0.43 m, squat match 0.10, peak joint speed 8.4 rad/s (accel 331), peak pelvis |vz| 0.56 m/s, max pelvis z 0.78 m
- stance: torso tilt 0.7 deg, pelvis tilt 0.4 deg, template 0.95; from a standing start: template 0.97, still standing 100%
- feet: 5.0 touchdowns while rising, 1.0 after standing, foot travel after standing 0.11 m, peak foot force 412 N
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, OK standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9), X no balance stepping after standing (foot travel <= 0.05 m), X no stomping while rising (touchdowns <= 4), OK no hard foot impacts (peak force <= 500 N)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 7.5, "squat_std": 0.12, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.9, "stand_prob": 0.4, "squat_prob": 0.225, "w_feet_move_stand": -30.0, "w_feet_move_rise": -1.5, "w_foot_impact": -2.0}`
- next round changes:
  - w_squat 7.5 -> 11.25 (squat match 0.10)
  - squat_prob 0.225 -> 0.275 (squat match 0.10)
  - squat_std 0.12 -> 0.16 (squat match 0.10: widen the kernel so the reward has a gradient)
  - w_feet_move_stand -30.0 -> -45.0 (balance stepping: feet travel 0.11 m after standing)
  - w_feet_move_rise -1.5 -> -2.25 (stomping: 5.0 touchdowns while rising)

## Manual decision after round 4 (2026-10-21 13:50)

- harness crashed computing round 5 knobs (KeyError for a knob added mid-run; fixed).
- round 4 (score 7.55) is taken as the base instead of round 2 (8.23): round 2 was trained with the 0.2 m feet-spread cliff and collapsed when continued; round 4 has the best stance so far (torso 0.7 deg, template 0.95) and loses points only on stepping (foot travel 0.11 m, 5 touchdowns while rising).
- stepping fix: the no-stepping penalty is now off only within 1 s after a training push (push_grace), instead of the leaky pelvis-speed gate.
- next round changes:
  - w_squat 7.5 -> 11.25 (squat match 0.10)
  - squat_prob 0.225 -> 0.275 (squat match 0.10)
  - squat_std 0.12 -> 0.16 (squat match 0.10: widen the kernel so the reward has a gradient)
  - w_feet_move_stand -30.0 -> -45.0 (balance stepping: feet travel 0.11 m after standing)
  - w_feet_move_rise -1.5 -> -2.25 (stomping: 5.0 touchdowns while rising)

## Round 5  (2026-10-21 14:27)  score 9.43  **best so far**

- run `2026-10-21_13-42-18_auto_r05`, checkpoint `model_23499.pt`; video `videos/getup/auto_r05.mp4`
- success 100%, time-to-stand median 2.45 s; per pose: supine 2.38 s (100%), face-down 2.50 s (100%), left side 2.64 s (100%), right side 2.33 s (100%)
- feet distance while rising 0.39 m, squat match 0.42, peak joint speed 9.7 rad/s (accel 339), peak pelvis |vz| 0.56 m/s, max pelvis z 0.77 m
- stance: torso tilt 1.0 deg, pelvis tilt 0.8 deg, template 0.87; from a standing start: template 0.94, still standing 100%
- feet: 4.0 touchdowns while rising, 0.0 after standing, foot travel after standing 0.07 m, peak foot force 417 N
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, X standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9), X no balance stepping after standing (foot travel <= 0.05 m), OK no stomping while rising (touchdowns <= 4), OK no hard foot impacts (peak force <= 500 N)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 11.25, "squat_std": 0.16, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.9, "stand_prob": 0.4, "squat_prob": 0.275, "w_feet_move_stand": -45.0, "w_feet_move_rise": -2.25, "w_foot_impact": -2.0, "feet_still_body_speed": null, "push_grace": 1.0, "feet_spread_ramp": 0.45, "w_floor_stall": -5.0}`
- next round changes:
  - w_squat 11.25 -> 16.875 (squat match 0.42)
  - squat_prob 0.275 -> 0.3 (squat match 0.42)
  - w_stand_template 6.9 -> 8.97 (stance: tilt 1.0 deg, template 0.87, from standing 0.94)
  - w_feet_move_stand -45.0 -> -67.5 (balance stepping: feet travel 0.07 m after standing)

## Harness restarted after round 5 (2026-10-21 14:29): new targets for upper-body sway after standing (user saw a slow sway in auto_r04: measured 4.3 / 3.5 cm fore-aft / sideways p-p at ~0.7 Hz from a standing start) and new reward terms torso_still / arm_still; rounds 4-5 re-measured, continuing from round 5 (score 8.67)

- next round changes:
  - w_squat 11.25 -> 16.875 (squat match 0.40)
  - squat_prob 0.275 -> 0.3 (squat match 0.40)
  - w_stand_template 6.9 -> 8.97 (stance: tilt 1.0 deg, template 0.87, from standing 0.93)
  - w_feet_move_stand -45.0 -> -67.5 (balance stepping: feet travel 0.07 m after standing)
  - w_feet_move_rise -2.25 -> -3.375 (stomping: 5.0 touchdowns while rising)
  - w_torso_still -10.0 -> -15.0 (upper-body sway 1.0 cm (from falls) / 1.7 cm (standing start) peak-to-peak)
  - w_arm_still -1.0 -> -1.5 (upper-body sway 1.0 cm (from falls) / 1.7 cm (standing start) peak-to-peak)

## Fix during round 6 (2026-10-21, manual): squat reward hacking - round 6 stopped at ~iteration 24100 and redone

- Symptom (training curve): squat_template rose to 7-9 per s while stand_template fell to ~0 and stand_up from 9.6
  to 5.3 - the robots stayed in the squat for the whole episode.
- Cause: the squat reward had no time limit; with w_squat 16.9 and the standing-only penalties (feet still, torso
  still, arm still) squatting forever paid more than standing up.
- Fix: squat reward only while the rising schedule runs (episode clock < sched_delay + sched_duration); the
  floor_stall penalty now covers any pelvis height below 0.62 m (knob stall_height) after the schedule + 0.5 s.
- Round 6 restarts from round 5 (model_23499) with the same knobs.

## Fix 2 during round 6 (2026-10-21, manual): gate exploitation - round 6 redone again

- Symptom (redo with the time-limited squat reward): stand_up 5-6.6, standing_posture / stance / feet_planted /
  stand_template ~0, floor_stall -4.2/s - robots crouched at pelvis 0.55-0.6 m, just under the 0.65 m
  "standing" gate (even the 40% standing starts left the stance).
- Cause: feet_move_stand / torso_still / arm_still only applied while "standing tall" (pelvis > 0.65 m, upright);
  with their weights raised (-67.5 / -15 / -1.5) not standing became the cheapest way out of all of them. Same
  pattern as round 3 (a state gate that can be escaped).
- Fix: these three penalties are now gated by the episode clock (schedule end + 0.5 s = 3.5 s) and "not fallen"
  (pelvis > 0.4 m) only, with the push grace kept; redo uses moderate weights (-45 / -10 / -0.5).
- The harness watchdog (stand_up < 8 for 200 iterations -> stop the round) is now in place for such collapses.

## Round 6 stopped by the watchdog (2026-10-21 15:21): stand_up reward 4.04 < 8.0 for 208 iterations (it 24044)

## Fix 3 during round 6 (2026-10-21, manual): stillness as a bonus, not a penalty - round 6 redone a third time

- Symptom (attempt 3, clock-gated stillness penalties excluding pelvis < 0.4 m): within ~50 iterations from the
  round-5 policy (100% get-up) almost all robots lay on the floor (floor_stall -4.5/s, stand_up 0.25); later the
  policy flailed (arm_still -11/s, feet -13/s, action std 0.41 -> 0.84).
- Cause: "pelvis < 0.4 m is exempt" was one more escape hatch - lying down avoided every stillness penalty.
  Lesson (rounds 3, 6a, 6b, 6c): a penalty attached to a desired state (standing) teaches the policy to leave it.
- Fix: torso_still / arm_still / clock gating removed (weights 0); new POSITIVE bounded term still_bonus (w 6),
  paid only while standing tall: mean of exp(-(torso speed/0.05)^2), exp(-(torso ang. speed/0.3)^2),
  exp(-(sum arm joint speed^2)/1). Leaving the stance only loses it. feet_move_stand back to the round-5 form (-45).
  The sway rule now raises w_still_bonus (x1.3, max 15).

- (manual) round 7 knobs: the watchdog relaxation (feet_spread, squat, rise_schedule, joint_speed_cap) was reverted to round 5 values - the round-6 failures came from the stillness penalties, not from these terms.

## Round 7 stopped by the watchdog (2026-10-21 15:38): stand_up reward 5.53 < 8.0 for 200 iterations (it 24036)

## Root cause of the repeated collapses (2026-10-21 16:30, controlled tests)

- Rounds 6 (three attempts) and 7 all collapsed within ~50 iterations (robots on the floor). Controlled tests:
  the round-5 policy, run WITHOUT learning in the training config (with sampled actions), stands 100%; resuming
  training from it with the exact round-5 config (test A) or from its intermediate checkpoint (C) collapses too,
  while resuming from round 4 (D, round 5's own start) does not.
- Decisive test: resume from round 5 without random initial episode clocks: lr 1e-3 (E1) collapses
  (stand_up 0.95, floor_stall -4.25), lr 3e-4 (E2) stays healthy (stand_up 9.6, floor_stall -0.02).
- Cause: rsl_rl's adaptive learning rate is not stored in checkpoints; every warm start restarted at lr 1e-3,
  too large for a converged policy - whether a round survived was luck. The reward explanations given for
  attempts 6b / 6c / 7 were therefore at most secondary (6a's squat hacking was a real reward exploit).
- Fix: every round now starts at lr 3e-4 (harness --lr) with GETUP_NO_RANDOM_EP_LEN=1. The stillness bonus and
  the other reward changes are kept (they are sound designs); round 8 continues from round 5.

- (manual) round 7 knobs: the watchdog relaxation (feet_spread, squat, rise_schedule, joint_speed_cap) was reverted to round 5 values - the round-6 failures came from the stillness penalties, not from these terms.

## Round 8  (2026-10-21 16:38)  score 8.61

- run `2026-10-21_15-59-18_auto_r08`, checkpoint `model_24998.pt`; video `videos/getup/auto_r08.mp4`
- success 100%, time-to-stand median 2.10 s; per pose: supine 2.22 s (100%), face-down 2.02 s (100%), left side 2.26 s (100%), right side 1.82 s (100%)
- feet distance while rising 0.44 m, squat match 0.40, peak joint speed 9.6 rad/s (accel 327), peak pelvis |vz| 0.63 m/s, max pelvis z 0.77 m
- stance: torso tilt 1.0 deg, pelvis tilt 0.6 deg, template 0.86; from a standing start: template 0.97, still standing 100%
- feet: 4.0 touchdowns while rising, 0.0 after standing, foot travel after standing 0.09 m, peak foot force 391 N
- upper-body sway after standing: 2.2 cm p-p from falls, 1.5 cm from a standing start; torso angular speed RMS 0.02 / 0.02 rad/s
- targets: OK success >= 0.97, OK time-to-stand median 2.0-3.5 s, OK every pose >= 1.8 s, OK feet distance while rising <= 0.45 m, X squat match >= 0.5, OK peak joint speed <= 10 rad/s, OK torso tilt <= 3 deg, X standing template >= 0.9, OK keeps stance from a standing start (template >= 0.9), X no balance stepping after standing (foot travel <= 0.05 m), OK no stomping while rising (touchdowns <= 4), OK no hard foot impacts (peak force <= 500 N), X still upper body after standing (sway <= 1.5 cm p-p), X still upper body from a standing start (sway <= 1.5 cm p-p)
- knobs: `{"sched_delay": 0.5, "sched_duration": 2.5, "sched_tol": 0.03, "t_gate": 2.5, "w_rise_schedule": -1000.0, "w_feet_spread": -120.0, "feet_max_dist": 0.35, "w_squat": 11.25, "squat_std": 0.16, "w_joint_speed_cap": -0.2, "joint_max_speed": 5.0, "w_stand_template": 6.9, "stand_prob": 0.4, "squat_prob": 0.275, "w_feet_move_stand": -45.0, "w_feet_move_rise": -2.25, "w_foot_impact": -2.0, "feet_still_body_speed": null, "push_grace": 1.0, "feet_spread_ramp": 0.45, "w_floor_stall": -5.0, "stall_height": 0.62, "stillness_time_only": false, "w_still_bonus": 6.0, "w_torso_still": 0.0, "w_arm_still": 0.0}`
- next round changes:
  - w_squat 11.25 -> 16.875 (squat match 0.40)
  - squat_prob 0.275 -> 0.3 (squat match 0.40)
  - w_stand_template 6.9 -> 8.97 (stance: tilt 1.0 deg, template 0.86, from standing 0.97)
  - w_feet_move_stand -45.0 -> -67.5 (balance stepping: feet travel 0.09 m after standing)
  - w_still_bonus 6.0 -> 7.8 (upper-body sway 2.2 cm (from falls) / 1.5 cm (standing start) peak-to-peak)

- (manual, before round 9) still_bonus kernels widened 3x (still_sigma_scale 3: 0.15 m/s, 0.9 rad/s, 3 (rad/s)^2):
  in round 8 the bonus paid 0.14 of max 6 - under the training action noise the narrow kernels were ~0 everywhere.

