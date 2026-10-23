# Round 14 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_10-10-11_flipauto_r14`, best checkpoint `model_12000.pt` (score 9.61), evaluated: model_12000.pt 9.61, model_12500.pt 9.606, model_12998.pt 9.591

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.61 | 9.55 | +0.06 |
| robot_rotation_deg | 364.9 | 366.9 | -2 |
| robot_max_rotation_deg | 366.5 | 367.0 | -0.5 |
| robot_peak_pelvis_m | 1.118 | 1.148 | -0.03 |
| pelvis_rise_m | 0.344 | 0.373 | -0.029 |
| robot_airborne_s | 0.56 | 0.58 | -0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 1.9 | 2.9 | -1 |
| early_fall | False | False |  |
| plane_dev_max_deg | 6.4 | 9.3 | -2.9 |
| plane_dev_mean_deg | 2.9 | 4.1 | -1.2 |
| leg_asym_deg | 2.1 | 2.0 | +0.1 |
| leg_err_deg | 5.2 | 4.8 | +0.4 |
| feet_dist_max_m | 0.207 | 0.212 | -0.005 |
| feet_dist_touchdown_m | 0.207 | 0.21 | -0.003 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 0 | 1 | -1 |
| flight_hip_err_rad | -0.11 | -0.07 | -0.04 |
| rot_at_ref_landing_deg | 322.3 | 329.8 | -7.5 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.729 | 0.744 | -0.015 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.162 | 0.165 | -0.003 |
| flight_hip_mean_rad | -1.65 | -1.62 | -0.03 |
| flight_knee_max_rad | 1.62 | 1.54 | +0.08 |
| flight_knee_overfold_rad | 0.33 | 0.27 | +0.06 |
| knee_sep_min_m | 0.181 | 0.174 | +0.007 |
| track_body_err_m | 0.0638 | 0.073 | -0.0092 |
| track_joint_err | 1.5039 | 1.5233 | -0.0194 |
| knee_sep_max_m | 0.277 | 0.269 | +0.008 |
| flight_hip_roll_max_rad | 0.17 | 0.19 | -0.02 |
| flight_hip_yaw_max_rad | 0.3 | 0.28 | +0.02 |
| stand_arm_vel_rms | 0.803 | 0.661 | +0.142 |
| stand_action_change | 0.0527 | 0.0392 | +0.0135 |
| stand_pelvis_speed | 0.076 | 0.047 | +0.029 |
| stand_torso_angvel | 0.399 | 0.201 | +0.198 |

## A2. Robustness (success = rotation >= 330, upright, pelvis > 0.6 m at the end)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [359.6, 364.2, 369.4] | [1.8, 3.0, 4.1] |
| dr | 1.0 | 0.0 | [359.5, 364.5, 369.8] | [2.1, 3.7, 5.7] |
| delay1 | 0.695 | 0.258 | [287.6, 363.1, 461.8] | [5.1, 11.3, 122.4] |
| delay2 | 0.0 | 0.902 | [135.5, 430.7, 849.1] | [94.8, 125.3, 171.4] |
| kp085 | 1.0 | 0.0 | [359.6, 364.6, 370.3] | [2.7, 4.4, 6.4] |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 6 of 53 measurements beyond tolerance

- 2.9 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 44 deg (signed +44), step 60: robot +0.94 vs ref -0.20 rad
- 1.5 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 23 deg (signed +21), step 51: robot +0.30 vs ref -0.69 rad
- 1.2 body:knee - left_knee_link: mean 0.10 m, max 0.16 m
- 1.2 body:wrist_yaw - right_wrist_yaw_link: mean 0.09 m, max 0.17 m
- 1.2 joint:knee - left_knee_joint: mean |err| 18 deg (signed +18), step 25: robot +0.57 vs ref +0.09 rad
- 1.1 body:ankle_roll - left_ankle_roll_link: mean 0.09 m, max 0.17 m

**crouch**: 10 of 53 measurements beyond tolerance

- 3.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 54 deg (signed +54), step 82: robot +0.89 vs ref -0.21 rad
- 2.4 asymmetry:wrist_roll - left/right differ 32 deg vs reference 9 deg
- 1.7 joint:elbow - right_elbow_joint: mean |err| 26 deg (signed -26), step 90: robot +0.02 vs ref +1.13 rad
- 1.7 joint:waist_pitch - waist_pitch_joint: mean |err| 25 deg (signed -13), step 77: robot -0.10 vs ref +0.52 rad
- 1.6 joint:wrist_roll - right_wrist_roll_joint: mean |err| 24 deg (signed -24), step 90: robot -0.57 vs ref +0.29 rad
- 1.4 body:ankle_roll - right_ankle_roll_link: mean 0.11 m, max 0.24 m

**takeoff**: 23 of 51 measurements beyond tolerance

- 5.2 asymmetry:wrist_roll - left/right differ 62 deg vs reference 10 deg
- 4.5 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 67 deg (signed -67), step 97: robot -0.43 vs ref +1.07 rad
- 4.4 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 67 deg (signed +67), step 97: robot +0.84 vs ref -0.38 rad
- 3.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.31 m, max 0.41 m
- 3.3 joint:wrist_roll - right_wrist_roll_joint: mean |err| 50 deg (signed -50), step 94: robot -0.75 vs ref +0.21 rad
- 3.0 joint:elbow - right_elbow_joint: mean |err| 45 deg (signed -45), step 91: robot -0.16 vs ref +0.95 rad

**flight**: 16 of 51 measurements beyond tolerance

- 7.2 asymmetry:wrist_roll - left/right differ 78 deg vs reference 6 deg
- 4.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 70 deg (signed +70), step 107: robot +1.01 vs ref -0.43 rad
- 3.8 joint:wrist_roll - left_wrist_roll_joint: mean |err| 57 deg (signed -57), step 107: robot -0.99 vs ref +0.70 rad
- 2.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.23 m, max 0.49 m
- 2.7 body:ankle_roll - right_ankle_roll_link: mean 0.21 m, max 0.40 m
- 2.5 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 38 deg (signed +38), step 109: robot -0.16 vs ref -1.20 rad

**land**: 17 of 53 measurements beyond tolerance

- 2.8 joint:elbow - right_elbow_joint: mean |err| 42 deg (signed +42), step 121: robot +0.74 vs ref -0.44 rad
- 2.6 asymmetry:elbow - left/right differ 27 deg vs reference 1 deg
- 2.1 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 32 deg (signed -32), step 122: robot -1.73 vs ref -0.83 rad
- 2.1 jitter:waist_roll - waist_roll_joint: joint acceleration RMS 55 vs reference 4 rad/s^2
- 1.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.15 m, max 0.20 m
- 1.7 jitter:shoulder_pitch - right_shoulder_pitch_joint: joint acceleration RMS 135 vs reference 21 rad/s^2

**settle**: 8 of 54 measurements beyond tolerance

- 3.0 jitter:all - mean action change 0.149 (quiet < 0.05)
- 2.7 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 56 vs reference 2 rad/s^2
- 1.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 23 deg (signed +23), step 154: robot +0.64 vs ref -0.13 rad
- 1.4 jitter:knee - left_knee_joint: joint acceleration RMS 31 vs reference 2 rad/s^2
- 1.3 jitter:waist_pitch - waist_pitch_joint: joint acceleration RMS 26 vs reference 2 rad/s^2
- 1.2 jitter:shoulder_roll - left_shoulder_roll_joint: joint acceleration RMS 18 vs reference 0 rad/s^2

**stand_after**: 3 of 54 measurements beyond tolerance

- 3.1 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 47 deg (signed +47), step 162: robot +0.76 vs ref -0.13 rad
- 1.2 joint:wrist_roll - right_wrist_roll_joint: mean |err| 18 deg (signed -18), step 165: robot -0.44 vs ref -0.11 rad
- 1.2 joint:knee - left_knee_joint: mean |err| 17 deg (signed +17), step 170: robot +0.40 vs ref +0.06 rad

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.5 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.269 |
| 1.7 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.225 |
| 1.0 | joint:hip_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.408 |
| 1.6 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.249 |
| 1.4 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.323 |
| 1.2 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.39 |
| 1.4 | asymmetry:elbow:crouch | dyn_sym | 0.0 | 0.2 | 0.291 |
| 2.4 | asymmetry:wrist_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.126 |
| 2.4 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.121 |
| 3.0 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0718 |
| 1.5 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.265 |
| 1.1 | joint:knee:takeoff | dyn_joint | 0.0 | 0.3 | 0.376 |
| 2.8 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.102 |
| 3.9 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0453 |
| 2.0 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.194 |
| 1.1 | asymmetry:knee:takeoff | dyn_sym | 0.0 | 0.2 | 0.388 |
| 5.2 | asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.0106 |
| 1.4 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.304 |
| 1.9 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.195 |
| 1.3 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.328 |
| 1.7 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.234 |
| 3.8 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.0361 |
| 2.5 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.111 |
| 2.7 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.654 |
| 2.9 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0973 |
| 1.8 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.23 |
| 2.1 | asymmetry:shoulder_pitch:flight | dyn_sym | 0.0 | 0.2 | 0.165 |
| 7.2 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.00182 |
| 1.1 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.417 |
| 1.9 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.217 |
| 2.6 | asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.0994 |
| 3.0 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 2.7 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.5 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0204 |
| 1.2 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.354 |
| 1.4 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.4 | joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.0207 |
| 3.1 | joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0658 |
| 2.8 | asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.0845 |
| 4.6 | joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0175 |
| 3.6 | joint:wrist_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.0441 |
| 2.9 | joint:wrist_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.0778 |
| 1.2 | body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.39 |
| 2.3 | joint:wrist_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.135 |
| 2.1 | joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.153 |
| 3.3 | joint:wrist_roll:takeoff | dyn_joint | 0.0 | 0.3 | 0.0551 |
| 1.5 | joint:wrist_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.269 |
| 1.8 | body:elbow:flight | dyn_body | 0.0 | 0.1 | 0.238 |
| 2.8 | joint:elbow:land | dyn_joint | 0.0 | 0.3 | 0.089 |
| 2.1 | jitter:waist_roll:land | dyn_quiet | 0.0 | 1.0 | - |

50 of 172 library checks fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.11| rad (end +0.01), reference max |0.10|
- arm joints mean |err| 6 deg; worst: left_shoulder_pitch 8, right_shoulder_pitch 8, left_shoulder_yaw 8, left_elbow 7
- action change mean 0.078 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 17, left_elbow 11, right_elbow 11, left_knee 10
- feet off the floor (> 6 cm): left 0, right 0 of 58 steps
- land (steps 121-129): pelvis speed mean 0.19 m/s, last 0.05; drift 0.02 m
- settle (steps 130-154): pelvis speed mean 0.15 m/s, last 0.02; drift 0.07 m
- stand_after (steps 155-187): pelvis speed mean 0.08 m/s, last 0.05; drift 0.04 m

## F. Training-config audit (what the training actually ran)

- 45 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 5

## F2. Knobs this round trained with vs round 13 (2 differences)

- tracking.scale: 2.25 -> 3.375
- tracking.std_scale: 0.722 -> 0.614

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r13: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x70e9ebb27ba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r14: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x726f2e02bba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] fidelity curriculum: r13: tracking weights x2.25, std x0.722
  r14: tracking weights x3.375, std x0.614

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
