# Round 8 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_09-59-11_cw2auto_r08`, best checkpoint `model_10493.pt` (score 5.84), evaluated: model_9500.pt 5.795, model_10000.pt 5.796, model_10493.pt 5.84

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 264.3 | 261.0 | +3.3 |
| robot_max_rotation_deg | 265.7 | 261.1 | +4.6 |
| robot_peak_pelvis_m | 0.774 | 0.772 | +0.002 |
| robot_airborne_s | 0.2 | 0.22 | -0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 17.3 | 17.6 | -0.3 |
| pelvis_rise_m | 0.027 | 0.05 | -0.023 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.629 | 0.627 | +0.002 |
| track_body_err_m | 0.04 | 0.0395 | +0.0005 |
| track_joint_err | 0.6112 | 0.5488 | +0.0624 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 2.6 | 2.2 | +0.4 |
| post_drift_m | 0.003 | 0.0 | +0.003 |
| post_sway_m | 0.002 | 0.0 | +0.002 |
| post_pelvis_speed_max | 0.001 | 0.0 | +0.001 |
| post_action_change | 0.0001 | 0.0 | +0.0001 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 2.5 | 2.2 | +0.3 |
| hold_height_err_m | 0.016 | 0.01 | +0.006 |
| hold_pose_err_rad | 0.058 | 0.049 | +0.009 |
| hold_pelvis_speed_max | 0.002 | 0.0 | +0.002 |
| hold_drift_m | 0.002 | 0.0 | +0.002 |
| hold_sway_m | 0.001 | 0.0 | +0.001 |
| hold_torso_angvel_rms | 0.001 | 0.0 | +0.001 |
| hold_action_change | 0.0002 | 0.0001 | +0.0001 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.84 | 5.842 | -0.002 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_09-59-11_cw2auto_r08/eval/_post_auto_model_10493.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.715 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_09-59-11_cw2auto_r08/eval/flip_auto_model_10493.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [249.5, 259.7, 269.3] | [11.9, 15.9, 19.0] |
| dr | 0.871 | 0.0 | [241.0, 257.8, 271.5] | [14.8, 18.8, 22.6] |
| delay1 | 0.664 | 0.0 | [227.0, 248.8, 270.9] | [16.4, 21.2, 26.0] |
| delay2 | 0.172 | 0.199 | [175.1, 253.5, 357.2] | [19.8, 26.8, 113.2] |
| kp085 | 0.828 | 0.004 | [241.0, 265.0, 286.4] | [14.5, 19.9, 25.2] |

## A3. Segment probe `10493` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 1.0 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 1.0 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 14 of 53 measurements beyond tolerance

- 2.4 asymmetry:shoulder_yaw - left/right differ 26 deg vs reference 1 deg
- 2.4 asymmetry:wrist_roll - left/right differ 25 deg vs reference 1 deg
- 1.9 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 28 deg (signed -28), step 6: robot -1.03 vs ref -0.38 rad
- 1.7 jitter:shoulder_yaw - right_shoulder_yaw_joint: joint acceleration RMS 60 vs reference 7 rad/s^2
- 1.5 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 30 vs reference 1 rad/s^2
- 1.5 body:ankle_roll - left_ankle_roll_link: mean 0.12 m, max 0.17 m

**lunge**: 7 of 51 measurements beyond tolerance

- 2.5 asymmetry:wrist_roll - left/right differ 34 deg vs reference 10 deg
- 1.8 body:ankle_roll - left_ankle_roll_link: mean 0.14 m, max 0.18 m
- 1.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.10 m, max 0.20 m
- 1.3 jitter:waist_yaw - waist_yaw_joint: joint acceleration RMS 56 vs reference 10 rad/s^2
- 1.2 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 21 vs reference 1 rad/s^2
- 1.1 body:knee - left_knee_link: mean 0.09 m, max 0.12 m

**support**: 16 of 51 measurements beyond tolerance

- 2.9 asymmetry:hip_yaw - left/right differ 43 deg vs reference 14 deg
- 2.2 joint:wrist_roll - left_wrist_roll_joint: mean |err| 33 deg (signed +16), step 59: robot +1.27 vs ref +0.37 rad
- 1.9 body:ankle_roll - right_ankle_roll_link: mean 0.15 m, max 0.47 m
- 1.9 asymmetry:wrist_roll - left/right differ 35 deg vs reference 16 deg
- 1.6 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 23 deg (signed -20), step 67: robot +0.70 vs ref +1.33 rad
- 1.5 body:wrist_yaw - left_wrist_yaw_link: mean 0.12 m, max 0.19 m

**land**: 18 of 53 measurements beyond tolerance

- 3.5 body:ankle_roll - left_ankle_roll_link: mean 0.28 m, max 0.46 m
- 2.9 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 43 deg (signed +43), step 84: robot +0.34 vs ref -0.80 rad
- 2.7 contact:right_foot - right_foot off the floor for 8 of 14 steps the reference has it down
- 2.6 body:knee - left_knee_link: mean 0.21 m, max 0.33 m
- 2.3 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 73 vs reference 6 rad/s^2
- 2.3 jitter:ankle_roll - right_ankle_roll_joint: joint acceleration RMS 102 vs reference 10 rad/s^2

**settle**: 3 of 54 measurements beyond tolerance

- 2.4 jitter:all - mean action change 0.121 (quiet < 0.05)
- 1.6 body:ankle_roll - left_ankle_roll_link: mean 0.13 m, max 0.18 m
- 1.0 joint:hip_roll - right_hip_roll_joint: mean |err| 16 deg (signed +16), step 95: robot -0.25 vs ref -0.69 rad

**stand_after**: 1 of 54 measurements beyond tolerance

- 1.0 body:ankle_roll - right_ankle_roll_link: mean 0.08 m, max 0.09 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.1 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.393 |
| 2.4 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.118 |
| 2.4 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.124 |
| 1.8 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.245 |
| 1.3 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.363 |
| 1.1 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.418 |
| 1.1 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.394 |
| 2.5 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.114 |
| 1.1 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.378 |
| 1.2 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.341 |
| 1.1 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.387 |
| 1.3 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.324 |
| 1.3 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.309 |
| 2.2 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.143 |
| 1.6 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.258 |
| 1.9 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.214 |
| 1.5 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.308 |
| 1.4 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.323 |
| 2.9 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0811 |
| 3.5 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0616 |
| 1.6 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.289 |
| 2.6 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.122 |
| 2.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 2.4 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.28 |
| 1.1 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.381 |
| 1.0 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.446 |
| 1.2 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.343 |
| 2.3 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.419 |
| 1.2 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.4 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.283 |
| 1.5 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.28 |
| 1.5 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.302 |
| 1.3 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.346 |
| 2.9 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.0771 |
| 1.7 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.277 |
| 2.0 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.171 |
| 2.3 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |

42 of 103 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.28| rad (end -0.13), reference max |0.51|
- arm joints mean |err| 2 deg; worst: right_elbow 5, left_shoulder_yaw 4, right_shoulder_roll 3, left_shoulder_roll 2
- action change mean 0.009 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 4, right_knee 3, right_hip_roll 2, left_shoulder_yaw 1
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.53 m/s, last 0.15; drift 0.08 m
- settle (steps 95-114): pelvis speed mean 0.35 m/s, last 0.25; drift 0.13 m
- stand_after (steps 115-489): pelvis speed mean 0.01 m/s, last 0.00; drift 0.06 m

## F. Training-config audit (what the training actually ran)

- 30 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 1, decider terms: 2

## F2. Knobs this round trained with vs round 7 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r7: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x717760b07d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r8: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x74e525c57d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r7: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0)]
  r8: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 2.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.3838, -0.0127]), rounds used 8, GPU 12.8 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.002 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.002 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.001 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.001 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.0 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 2.5 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.058 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.016 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.003 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 2.6 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 3.48 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.871 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.664 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.828 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 264.3 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/body:ankle_roll:land

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-199.jpg
- [ ] sheet_200-239.jpg
- [ ] sheet_240-279.jpg
- [ ] sheet_280-319.jpg
- [ ] sheet_320-359.jpg
- [ ] sheet_360-399.jpg
- [ ] sheet_400-439.jpg
- [ ] sheet_440-479.jpg
- [ ] sheet_480-519.jpg
- [ ] sheet_520-559.jpg
- [ ] sheet_560-599.jpg
- [ ] sheet_600-639.jpg
- [ ] sheet_640-679.jpg
- [ ] sheet_680-719.jpg
- [ ] sheet_720-737.jpg
