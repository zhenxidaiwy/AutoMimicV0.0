# Round 12 - quantitative report (step 1, before any diagnosis)

run `2026-11-02_02-02-03_cw2auto_r12`, best checkpoint `model_13500.pt` (score 5.808), evaluated: model_13000.pt 5.78, model_13500.pt 5.808, model_13999.pt 5.752

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 256.0 | 291.4 | -35.4 |
| robot_max_rotation_deg | 257.9 | 294.2 | -36.3 |
| robot_peak_pelvis_m | 0.778 | 0.775 | +0.003 |
| robot_airborne_s | 0.2 | 0.2 | +0 |
| landed_upright | True | True |  |
| end_tilt_deg | 14.4 | 15.1 | -0.7 |
| pelvis_rise_m | 0.052 | 0.073 | -0.021 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.616 | 0.624 | -0.008 |
| track_body_err_m | 0.0479 | 0.0561 | -0.0082 |
| track_joint_err | 0.5884 | 0.6286 | -0.0402 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 5.5 | 4.8 | +0.7 |
| post_drift_m | 0.0 | 0.007 | -0.007 |
| post_sway_m | 0.0 | 0.005 | -0.005 |
| post_pelvis_speed_max | 0.0 | 0.05 | -0.05 |
| post_action_change | 0.0 | 0.0179 | -0.0179 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 5.5 | 4.9 | +0.6 |
| hold_height_err_m | 0.015 | 0.025 | -0.01 |
| hold_pose_err_rad | 0.052 | 0.057 | -0.005 |
| hold_pelvis_speed_max | 0.0 | 0.051 | -0.051 |
| hold_drift_m | 0.0 | 0.002 | -0.002 |
| hold_sway_m | 0.0 | 0.005 | -0.005 |
| hold_torso_angvel_rms | 0.0 | 0.145 | -0.145 |
| hold_action_change | 0.0 | 0.018 | -0.018 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.808 | 5.776 | +0.032 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_02-02-03_cw2auto_r12/eval/_post_auto_model_13500.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.714 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_02-02-03_cw2auto_r12/eval/flip_auto_model_13500.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 1.0 | 1.0 | 0.0 | [241.0, 249.5, 260.0] | [13.2, 15.1, 17.4] | [0.0, 0.0, 0.001] |
| dr | 0.973 | 0.918 | 0.0 | [236.1, 251.6, 267.7] | [14.3, 17.7, 21.2] | [0.024, 0.11, 0.334] |
| delay1 | 0.965 | 0.871 | 0.004 | [246.6, 266.6, 283.1] | [14.9, 18.9, 24.3] | [0.026, 0.133, 0.447] |
| delay2 | 0.582 | 0.352 | 0.098 | [227.1, 271.2, 306.8] | [18.3, 24.7, 109.3] | [0.049, 0.361, 0.892] |
| kp085 | 0.914 | 0.844 | 0.004 | [228.8, 252.0, 269.0] | [14.3, 18.2, 24.5] | [0.015, 0.096, 0.359] |

## A3. Segment probe `13999` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 0.953 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 0.984 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 13 of 53 measurements beyond tolerance

- 2.4 asymmetry:hip_yaw - left/right differ 29 deg vs reference 5 deg
- 2.0 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 39 vs reference 1 rad/s^2
- 1.9 joint:knee - left_knee_joint: mean |err| 28 deg (signed +28), step 15: robot +0.74 vs ref +0.06 rad
- 1.8 joint:hip_yaw - left_hip_yaw_joint: mean |err| 26 deg (signed -26), step 11: robot -0.27 vs ref +0.27 rad
- 1.5 joint:hip_pitch - left_hip_pitch_joint: mean |err| 22 deg (signed -22), step 5: robot -0.94 vs ref -0.43 rad
- 1.4 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 22 deg (signed -22), step 15: robot -0.03 vs ref +0.46 rad

**lunge**: 7 of 51 measurements beyond tolerance

- 2.1 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 37 vs reference 1 rad/s^2
- 1.6 body:ankle_roll - left_ankle_roll_link: mean 0.13 m, max 0.17 m
- 1.3 jitter:wrist_yaw - right_wrist_yaw_joint: joint acceleration RMS 23 vs reference 1 rad/s^2
- 1.2 joint:wrist_roll - left_wrist_roll_joint: mean |err| 18 deg (signed +18), step 34: robot +0.52 vs ref -0.03 rad
- 1.2 body:wrist_yaw - right_wrist_yaw_link: mean 0.10 m, max 0.14 m
- 1.1 body:knee - left_knee_link: mean 0.09 m, max 0.12 m

**support**: 13 of 51 measurements beyond tolerance

- 3.2 body:ankle_roll - right_ankle_roll_link: mean 0.26 m, max 0.54 m
- 2.2 asymmetry:shoulder_yaw - left/right differ 41 deg vs reference 19 deg
- 2.1 joint:wrist_roll - right_wrist_roll_joint: mean |err| 31 deg (signed -18), step 63: robot -1.52 vs ref -0.21 rad
- 1.9 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 28 deg (signed -28), step 72: robot -0.58 vs ref +0.40 rad
- 1.5 body:wrist_yaw - left_wrist_yaw_link: mean 0.12 m, max 0.20 m
- 1.5 joint:hip_yaw - right_hip_yaw_joint: mean |err| 23 deg (signed +12), step 50: robot +0.72 vs ref -0.29 rad

**land**: 20 of 53 measurements beyond tolerance

- 5.2 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 89 vs reference 1 rad/s^2
- 3.7 body:ankle_roll - left_ankle_roll_link: mean 0.29 m, max 0.41 m
- 3.0 body:knee - left_knee_link: mean 0.24 m, max 0.31 m
- 2.9 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 43 deg (signed +43), step 83: robot +0.31 vs ref -0.79 rad
- 2.4 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 76 vs reference 6 rad/s^2
- 2.3 contact:right_foot - right_foot off the floor for 7 of 14 steps the reference has it down

**settle**: 8 of 54 measurements beyond tolerance

- 2.2 body:ankle_roll - left_ankle_roll_link: mean 0.18 m, max 0.25 m
- 2.2 jitter:all - mean action change 0.111 (quiet < 0.05)
- 1.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.11 m, max 0.12 m
- 1.3 body:knee - left_knee_link: mean 0.10 m, max 0.14 m
- 1.2 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 18 deg (signed +12), step 97: robot -0.11 vs ref -0.62 rad
- 1.1 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 31 vs reference 4 rad/s^2

**stand_after**: 1 of 54 measurements beyond tolerance

- 1.1 body:ankle_roll - right_ankle_roll_link: mean 0.08 m, max 0.09 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.4 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.12 |
| 1.3 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.315 |
| 1.0 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.401 |
| 1.0 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.412 |
| 1.2 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.342 |
| 1.6 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.269 |
| 1.2 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.381 |
| 1.1 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.421 |
| 1.0 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.413 |
| 1.3 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.317 |
| 1.1 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.372 |
| 1.5 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.27 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.345 |
| 1.9 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.192 |
| 2.1 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.164 |
| 3.2 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.0758 |
| 1.5 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.292 |
| 1.5 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.306 |
| 2.9 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0831 |
| 1.3 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.324 |
| 1.0 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.401 |
| 3.7 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0533 |
| 1.4 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.326 |
| 3.0 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.0901 |
| 2.3 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.2 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.355 |
| 2.2 | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.3 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 0.349 |
| 2.2 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.167 |
| 1.2 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.344 |
| 1.1 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.428 |
| 1.4 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.294 |
| 2.3 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 5.2 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 2.0 | 1.0 | - |
| 1.2 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.372 |
| 2.1 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.399 |
| 1.9 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.194 |
| 1.1 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.417 |
| 1.1 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.3 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.14 |
| 2.4 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.2 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.146 |
| 1.4 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.285 |

45 of 107 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.26| rad (end -0.15), reference max |0.51|
- arm joints mean |err| 2 deg; worst: right_shoulder_pitch 4, left_shoulder_pitch 2, right_shoulder_yaw 2, right_shoulder_roll 1
- action change mean 0.008 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_knee 2, right_ankle_pitch 2, right_wrist_roll 2, right_elbow 1
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.56 m/s, last 0.07; drift 0.11 m
- settle (steps 95-114): pelvis speed mean 0.24 m/s, last 0.28; drift 0.09 m
- stand_after (steps 115-489): pelvis speed mean 0.01 m/s, last 0.00; drift 0.09 m

## F. Training-config audit (what the training actually ran)

- 34 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 5, decider terms: 2

## F2. Knobs this round trained with vs round 11 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r11: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x78a18203fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r12: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7ff9dd67fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r11: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0)]
  r12: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_all_settle', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 2.0), ('lib_cartwheel_2_asymmetry_hip_yaw_support', 1.0), ('lib_cartwheel_2_asymmetry_wrist_roll_support', 1.0), ('agent_r

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [-0.0851, 0.1462]), rounds used 12, GPU 19.1 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.0 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.0 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.0 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.0 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.0 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 5.5 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.052 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.015 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.0 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 5.5 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 5.19 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.973 | >= 0.95 | pass |
| robust_latency_20ms | robust.delay1 | 0.965 | >= 0.95 | pass |
| robust_stiffness | robust.kp085 | 0.914 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 256.0 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/jitter:wrist_roll:land

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
