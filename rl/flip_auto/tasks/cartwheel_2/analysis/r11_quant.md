# Round 11 - quantitative report (step 1, before any diagnosis)

run `2026-11-02_00-12-37_cw2auto_r11`, best checkpoint `model_12500.pt` (score 5.776), evaluated: model_12500.pt 5.776, model_13000.pt 5.74, model_13491.pt 5.759

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 291.4 | 261.7 | +29.7 |
| robot_max_rotation_deg | 294.2 | 261.9 | +32.3 |
| robot_peak_pelvis_m | 0.775 | 0.767 | +0.008 |
| robot_airborne_s | 0.2 | 0.2 | +0 |
| landed_upright | True | True |  |
| end_tilt_deg | 15.1 | 13.3 | +1.8 |
| pelvis_rise_m | 0.073 | 0.046 | +0.027 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.624 | 0.625 | -0.001 |
| track_body_err_m | 0.0561 | 0.0517 | +0.0044 |
| track_joint_err | 0.6286 | 0.6344 | -0.0058 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 4.8 | 6.6 | -1.8 |
| post_drift_m | 0.007 | 0.0 | +0.007 |
| post_sway_m | 0.005 | 0.0 | +0.005 |
| post_pelvis_speed_max | 0.05 | 0.0 | +0.05 |
| post_action_change | 0.0179 | 0.0 | +0.0179 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 4.9 | 6.7 | -1.8 |
| hold_height_err_m | 0.025 | 0.018 | +0.007 |
| hold_pose_err_rad | 0.057 | 0.054 | +0.003 |
| hold_pelvis_speed_max | 0.051 | 0.0 | +0.051 |
| hold_drift_m | 0.002 | 0.0 | +0.002 |
| hold_sway_m | 0.005 | 0.0 | +0.005 |
| hold_torso_angvel_rms | 0.145 | 0.001 | +0.144 |
| hold_action_change | 0.018 | 0.0001 | +0.0179 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.776 | 5.793 | -0.017 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_00-12-37_cw2auto_r11/eval/_post_auto_model_12500.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.724 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_00-12-37_cw2auto_r11/eval/flip_auto_model_12500.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 1.0 | 1.0 | 0.0 | [264.4, 274.6, 284.6] | [12.7, 15.7, 19.1] | [0.0, 0.003, 0.008] |
| dr | 0.992 | 0.938 | 0.0 | [259.0, 275.0, 291.7] | [14.8, 18.2, 22.5] | [0.021, 0.113, 0.316] |
| delay1 | 0.961 | 0.805 | 0.008 | [255.3, 272.3, 286.5] | [16.0, 19.6, 23.6] | [0.026, 0.158, 0.429] |
| delay2 | 0.453 | 0.254 | 0.098 | [209.2, 267.2, 302.6] | [18.7, 23.0, 109.5] | [0.096, 0.471, 1.119] |
| kp085 | 0.988 | 0.93 | 0.0 | [267.8, 283.4, 302.1] | [15.1, 19.4, 24.1] | [0.021, 0.108, 0.35] |

## A3. Segment probe `13491` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 0.984 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 1.0 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 12 of 53 measurements beyond tolerance

- 2.1 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 32 deg (signed -32), step 8: robot -0.19 vs ref +0.49 rad
- 2.1 joint:knee - left_knee_joint: mean |err| 31 deg (signed +31), step 15: robot +0.86 vs ref +0.06 rad
- 2.0 asymmetry:hip_pitch - left/right differ 47 deg vs reference 27 deg
- 1.7 asymmetry:shoulder_yaw - left/right differ 19 deg vs reference 1 deg
- 1.6 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 32 vs reference 1 rad/s^2
- 1.4 body:wrist_yaw - right_wrist_yaw_link: mean 0.11 m, max 0.23 m

**lunge**: 13 of 51 measurements beyond tolerance

- 2.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.22 m, max 0.30 m
- 2.7 asymmetry:shoulder_roll - left/right differ 43 deg vs reference 16 deg
- 1.9 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 33 vs reference 1 rad/s^2
- 1.9 asymmetry:shoulder_pitch - left/right differ 30 deg vs reference 12 deg
- 1.8 asymmetry:wrist_roll - left/right differ 27 deg vs reference 10 deg
- 1.7 body:elbow - right_elbow_link: mean 0.13 m, max 0.18 m

**support**: 19 of 51 measurements beyond tolerance

- 3.9 asymmetry:wrist_roll - left/right differ 54 deg vs reference 16 deg
- 3.2 asymmetry:hip_yaw - left/right differ 46 deg vs reference 14 deg
- 2.4 joint:wrist_roll - left_wrist_roll_joint: mean |err| 36 deg (signed +34), step 60: robot +1.56 vs ref +0.34 rad
- 2.3 body:ankle_roll - right_ankle_roll_link: mean 0.18 m, max 0.47 m
- 2.0 joint:hip_yaw - left_hip_yaw_joint: mean |err| 30 deg (signed -27), step 53: robot -1.73 vs ref -0.11 rad
- 1.6 body:wrist_yaw - right_wrist_yaw_link: mean 0.13 m, max 0.23 m

**land**: 20 of 53 measurements beyond tolerance

- 3.1 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 53 vs reference 1 rad/s^2
- 3.0 contact:right_foot - right_foot off the floor for 9 of 14 steps the reference has it down
- 2.8 body:ankle_roll - left_ankle_roll_link: mean 0.22 m, max 0.32 m
- 2.6 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 38 deg (signed +38), step 83: robot +0.20 vs ref -0.79 rad
- 2.5 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 38 vs reference 0 rad/s^2
- 2.2 body:knee - left_knee_link: mean 0.18 m, max 0.23 m

**settle**: 9 of 54 measurements beyond tolerance

- 3.4 jitter:all - mean action change 0.169 (quiet < 0.05)
- 2.3 body:ankle_roll - left_ankle_roll_link: mean 0.19 m, max 0.23 m
- 1.7 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 46 vs reference 4 rad/s^2
- 1.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.11 m, max 0.14 m
- 1.3 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 20 deg (signed +13), step 97: robot -0.05 vs ref -0.62 rad
- 1.2 joint:hip_roll - right_hip_roll_joint: mean |err| 18 deg (signed +18), step 102: robot -0.15 vs ref -0.69 rad

**stand_after**: 1 of 54 measurements beyond tolerance

- 1.1 body:ankle_roll - right_ankle_roll_link: mean 0.09 m, max 0.13 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.1 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.373 |
| 1.7 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.22 |
| 1.1 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.395 |
| 1.1 | cartwheel_2/joint:wrist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.377 |
| 1.3 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.365 |
| 2.7 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.112 |
| 1.2 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.37 |
| 1.8 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.213 |
| 1.5 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.276 |
| 1.4 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.289 |
| 2.0 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.176 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.336 |
| 1.2 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 0.366 |
| 1.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.396 |
| 2.4 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.126 |
| 1.1 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.389 |
| 2.3 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.158 |
| 1.6 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.268 |
| 1.6 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.27 |
| 2.6 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.107 |
| 2.8 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.107 |
| 1.1 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.431 |
| 2.2 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.171 |
| 1.2 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.358 |
| 3.0 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.3 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.32 |
| 3.4 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.344 |
| 1.4 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 0.319 |
| 2.3 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.156 |
| 1.1 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.408 |
| 1.5 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.261 |
| 2.5 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 3.1 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 1.4 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.328 |
| 1.9 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.7 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.227 |
| 2.1 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.161 |
| 1.4 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.318 |
| 3.2 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.0595 |
| 1.2 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.241 |
| 1.6 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.34 |
| 3.9 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.2 | 0.0344 |
| 2.1 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.155 |
| 2.7 | cartwheel_2/asymmetry:shoulder_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.0933 |

48 of 107 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.29| rad (end -0.11), reference max |0.51|
- arm joints mean |err| 2 deg; worst: left_shoulder_pitch 4, left_shoulder_yaw 4, right_shoulder_roll 2, right_elbow 2
- action change mean 0.028 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_knee 6, right_ankle_pitch 6, right_hip_roll 5, right_hip_yaw 4
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.54 m/s, last 0.12; drift 0.07 m
- settle (steps 95-114): pelvis speed mean 0.23 m/s, last 0.36; drift 0.08 m
- stand_after (steps 115-489): pelvis speed mean 0.05 m/s, last 0.04; drift 0.08 m

## F. Training-config audit (what the training actually ran)

- 31 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 2, decider terms: 2

## F2. Knobs this round trained with vs round 10 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r10: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x73404651bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r11: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x78a18203fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r10: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0), ('agent_r10_hold_posture', 1.0)]
  r11: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.1634, -0.0851]), rounds used 11, GPU 17.5 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.051 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.002 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.005 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.145 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.018 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 4.9 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.057 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.025 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.007 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 4.8 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 3.86 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.992 | >= 0.95 | pass |
| robust_latency_20ms | robust.delay1 | 0.961 | >= 0.95 | pass |
| robust_stiffness | robust.kp085 | 0.988 | >= 0.95 | pass |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 291.4 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/asymmetry:wrist_roll:support

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
