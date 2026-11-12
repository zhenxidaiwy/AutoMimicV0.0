# Round 3 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_00-55-49_cw2auto_r03`, best checkpoint `model_2998.pt` (score 5.642), evaluated: model_2000.pt 1.72, model_2500.pt 5.604, model_2998.pt 5.642

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 254.5 | 232.5 | +22 |
| robot_max_rotation_deg | 255.7 | 234.1 | +21.6 |
| robot_peak_pelvis_m | 0.774 | 0.696 | +0.078 |
| robot_airborne_s | 0.24 | 0.08 | +0.16 |
| landed_upright | True | False |  |
| end_tilt_deg | 15.8 | 76.8 | -61 |
| pelvis_rise_m | 0.014 | 0.063 | -0.049 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.567 | 0.169 | +0.398 |
| track_body_err_m | 0.0875 | 0.6927 | -0.605 |
| track_joint_err | 1.175 | 3.8967 | -2.72 |
| post_fell | False | True |  |
| post_tilt_err_max_deg | 4.5 | 73.4 | -68.9 |
| post_drift_m | 0.007 | 0.25 | -0.243 |
| post_sway_m | 0.004 | 0.211 | -0.207 |
| post_pelvis_speed_max | 0.021 | 0.726 | -0.705 |
| post_action_change | 0.0008 | 0.1243 | -0.123 |
| post_feet_off_steps | 0 | 250 | -250 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | True |  |
| hold_tilt_err_max_deg | 5.3 | 77.4 | -72.1 |
| hold_height_err_m | 0.032 | 0.57 | -0.538 |
| hold_pose_err_rad | 0.098 | 0.353 | -0.255 |
| hold_pelvis_speed_max | 0.326 | 1.112 | -0.786 |
| hold_drift_m | 0.039 | 0.499 | -0.46 |
| hold_sway_m | 0.041 | 0.264 | -0.223 |
| hold_torso_angvel_rms | 0.19 | 3.123 | -2.93 |
| hold_action_change | 0.0125 | 0.5776 | -0.565 |
| hold_feet_off_steps | 0 | 199 | -199 |
| early_fall | False | False |  |
| score | 5.642 | 1.82 | +3.82 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_00-55-49_cw2auto_r03/eval/_post_auto_model_2998.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.725 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_00-55-49_cw2auto_r03/eval/flip_auto_model_2998.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 0.988 | 0.0 | [244.7, 257.9, 278.2] | [13.0, 16.1, 20.9] |
| dr | 0.754 | 0.0 | [239.7, 254.6, 276.0] | [16.4, 19.7, 23.2] |
| delay1 | 0.652 | 0.043 | [235.5, 258.2, 288.5] | [17.8, 21.8, 26.4] |
| delay2 | 0.078 | 0.578 | [193.8, 280.2, 473.0] | [22.8, 104.3, 139.5] |
| kp085 | 0.66 | 0.008 | [241.7, 264.1, 292.6] | [16.3, 20.8, 26.1] |

## A3. Segment probe `2998` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [130, 238, 238] | 238 | stand | 0.781 |
| 16 | lunge | [209, 222, 222] | 238 | stand | 0.859 |
| 30 | lunge | [208, 208, 208] | 238 | stand | 0.953 |
| 46 | support | [192, 192, 192] | 238 | stand | 1.0 |
| 60 | support | [172, 178, 178] | 238 | stand | 0.875 |
| 81 | land | [19, 120, 157] | 201 | stand | 0.391 |
| 95 | settle | [143, 143, 143] | 238 | stand | 1.0 |
| 115 | stand | [123, 123, 123] | 238 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 14 of 53 measurements beyond tolerance

- 4.7 contact:left_foot - left_foot off the floor for 14 of 16 steps
- 2.9 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 57 vs reference 1 rad/s^2
- 2.3 asymmetry:hip_pitch - left/right differ 50 deg vs reference 27 deg
- 1.9 joint:knee - left_knee_joint: mean |err| 29 deg (signed +29), step 15: robot +0.88 vs ref +0.06 rad
- 1.9 body:knee - left_knee_link: mean 0.15 m, max 0.22 m
- 1.8 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 28 deg (signed -28), step 15: robot -0.19 vs ref +0.46 rad

**lunge**: 12 of 51 measurements beyond tolerance

- 2.8 body:ankle_roll - left_ankle_roll_link: mean 0.23 m, max 0.26 m
- 2.4 asymmetry:shoulder_pitch - left/right differ 36 deg vs reference 12 deg
- 2.3 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 40 vs reference 1 rad/s^2
- 1.9 body:knee - left_knee_link: mean 0.15 m, max 0.21 m
- 1.8 asymmetry:wrist_roll - left/right differ 27 deg vs reference 10 deg
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.23 m

**support**: 24 of 51 measurements beyond tolerance

- 3.6 body:ankle_roll - right_ankle_roll_link: mean 0.29 m, max 0.50 m
- 3.5 joint:elbow - left_elbow_joint: mean |err| 52 deg (signed -51), step 55: robot -0.51 vs ref +1.38 rad
- 3.1 body:wrist_yaw - left_wrist_yaw_link: mean 0.24 m, max 0.29 m
- 2.9 body:elbow - left_elbow_link: mean 0.23 m, max 0.35 m
- 2.8 body:shoulder_roll - left_shoulder_roll_link: mean 0.22 m, max 0.33 m
- 2.6 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 39 deg (signed +39), step 65: robot -0.22 vs ref -1.32 rad

**land**: 23 of 53 measurements beyond tolerance

- 5.1 body:ankle_roll - left_ankle_roll_link: mean 0.41 m, max 0.59 m
- 3.5 body:knee - left_knee_link: mean 0.28 m, max 0.39 m
- 3.3 contact:left_foot - left_foot off the floor for 10 of 14 steps
- 3.3 contact:right_foot - right_foot off the floor for 10 of 14 steps
- 3.0 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 47 vs reference 0 rad/s^2
- 2.9 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 50 vs reference 1 rad/s^2

**settle**: 5 of 54 measurements beyond tolerance

- 3.0 body:ankle_roll - left_ankle_roll_link: mean 0.24 m, max 0.31 m
- 2.0 jitter:all - mean action change 0.101 (quiet < 0.05)
- 1.7 body:knee - left_knee_link: mean 0.13 m, max 0.18 m
- 1.1 joint:hip_roll - right_hip_roll_joint: mean |err| 16 deg (signed +16), step 95: robot -0.22 vs ref -0.69 rad
- 1.0 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 15 deg (signed +1), step 114: robot -0.17 vs ref +0.47 rad

**stand_after**: 5 of 54 measurements beyond tolerance

- 1.5 asymmetry:shoulder_yaw - left/right differ 20 deg vs reference 5 deg
- 1.4 joint:wrist_pitch - left_wrist_pitch_joint: mean |err| 21 deg (signed +21), step 151: robot +0.70 vs ref +0.25 rad
- 1.4 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 20 deg (signed -20), step 123: robot -0.18 vs ref +0.49 rad
- 1.3 body:ankle_roll - right_ankle_roll_link: mean 0.11 m, max 0.21 m
- 1.2 joint:knee - right_knee_joint: mean |err| 18 deg (signed +18), step 115: robot +0.76 vs ref +0.10 rad

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.2 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.337 |
| 4.7 | cartwheel_2/contact:left_foot:stand | dyn_contact | 0.0 | None | - |
| 1.1 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.377 |
| 2.8 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.105 |
| 1.7 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.248 |
| 1.9 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.215 |
| 1.0 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.412 |
| 1.8 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.212 |
| 1.9 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.194 |
| 1.2 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.341 |
| 1.4 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.307 |
| 1.7 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.231 |
| 1.3 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.315 |
| 1.5 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.271 |
| 2.3 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.132 |
| 2.6 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.106 |
| 3.6 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.0546 |
| 3.1 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.0871 |
| 2.3 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.159 |
| 2.3 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.132 |
| 1.6 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.249 |
| 5.1 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0166 |
| 2.8 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.103 |
| 3.5 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.0617 |
| 3.3 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.0 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.413 |
| 2.0 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.263 |
| 1.5 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.272 |
| 3.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.093 |
| 2.2 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.145 |
| 1.3 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.343 |
| 3.5 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.0472 |
| 3.3 | cartwheel_2/contact:left_foot:land | dyn_contact | 0.0 | None | - |
| 3.0 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.0983 |

38 of 92 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 9

- 2.8 body:shoulder_roll:support - left_shoulder_roll_link: mean 0.22 m, max 0.33 m
- 2.6 joint:hip_pitch:land - left_hip_pitch_joint: mean |err| 38 deg (signed -38), step 84: robot -1.14 vs ref -0.11 rad
- 2.4 asymmetry:shoulder_pitch:lunge - left/right differ 36 deg vs reference 12 deg
- 2.3 asymmetry:hip_pitch:stand - left/right differ 50 deg vs reference 27 deg
- 2.3 jitter:wrist_roll:lunge - right_wrist_roll_joint: joint acceleration RMS 40 vs reference 1 rad/s^2
- 2.2 body:torso:support - torso_link: mean 0.18 m, max 0.29 m
- 2.2 body:hip_roll:support - left_hip_roll_link: mean 0.17 m, max 0.26 m
- 2.1 body:pelvis:support - pelvis: mean 0.17 m, max 0.28 m
- 2.0 jitter:ankle_pitch:land - right_ankle_pitch_joint: joint acceleration RMS 263 vs reference 38 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.24| rad (end -0.19), reference max |0.51|
- arm joints mean |err| 4 deg; worst: left_shoulder_yaw 8, right_shoulder_yaw 7, left_shoulder_roll 5, left_elbow 5
- action change mean 0.037 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 8, right_hip_yaw 7, left_knee 7, left_hip_yaw 6
- feet off the floor (> 6 cm): left 0, right 0 of 145 steps
- land (steps 81-94): pelvis speed mean 0.41 m/s, last 0.23; drift 0.01 m
- settle (steps 95-114): pelvis speed mean 0.08 m/s, last 0.09; drift 0.01 m
- stand_after (steps 115-239): pelvis speed mean 0.09 m/s, last 0.02; drift 0.14 m

## F. Training-config audit (what the training actually ran)

- 27 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 0, decider terms: 0

## F2. Knobs this round trained with vs round 2 (3 differences)

- prior.lunge: - -> 3.0
- prior.support: - -> 2.0
- reference.variant: "plant_vlm_hold" -> "reachqp_vlm_hold"

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r2: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7792b6ec3d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r3: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x73e88547bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [-0.0196, 0.8737]), rounds used 3, GPU 4.7 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.326 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.039 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.041 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.19 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.013 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 5.3 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.098 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.032 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.007 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 4.5 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 5.12 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.754 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.652 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.66 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 254.5 | >= 229.95000000000002 | pass |
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
- [ ] sheet_480-487.jpg
