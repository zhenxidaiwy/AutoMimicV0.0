# Round 11 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_05-54-33_flipauto_r11`, best checkpoint `model_9499.pt` (score 9.433), evaluated: model_8500.pt 9.398, model_9000.pt 9.397, model_9499.pt 9.433

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.433 | 7.414 | +2.02 |
| robot_rotation_deg | 371.2 | 353.2 | +18 |
| robot_max_rotation_deg | 371.4 | 361.2 | +10.2 |
| robot_peak_pelvis_m | 1.176 | 1.167 | +0.009 |
| pelvis_rise_m | 0.421 | 0.389 | +0.032 |
| robot_airborne_s | 0.58 | 0.58 | +0 |
| landed_upright | True | True |  |
| end_tilt_deg | 6.4 | 18.3 | -11.9 |
| early_fall | False | False |  |
| plane_dev_max_deg | 5.3 | 9.1 | -3.8 |
| plane_dev_mean_deg | 3.2 | 4.8 | -1.6 |
| leg_asym_deg | 2.2 | 1.9 | +0.3 |
| leg_err_deg | 4.9 | 5.1 | -0.2 |
| feet_dist_max_m | 0.218 | 0.232 | -0.014 |
| feet_dist_touchdown_m | 0.198 | 0.203 | -0.005 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 1 | 1 | +0 |
| flight_hip_err_rad | -0.04 | -0.11 | +0.07 |
| rot_at_ref_landing_deg | 324.1 | 320.5 | +3.6 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.746 | 0.738 | +0.008 |
| stand_stable | True | False |  |
| stand_feet_d_end | 0.301 | 0.349 | -0.048 |
| flight_hip_mean_rad | -1.58 | -1.65 | +0.07 |
| flight_knee_max_rad | 1.56 | 1.67 | -0.11 |
| flight_knee_overfold_rad | 0.26 | 0.32 | -0.06 |
| knee_sep_min_m | 0.18 | 0.182 | -0.002 |
| track_body_err_m | 0.1056 | 0.104 | +0.0016 |
| track_joint_err | 2.0797 | 2.1392 | -0.0595 |
| knee_sep_max_m | 0.287 | 0.279 | +0.008 |
| flight_hip_roll_max_rad | 0.19 | 0.1 | +0.09 |
| flight_hip_yaw_max_rad | 0.23 | 0.25 | -0.02 |
| stand_arm_vel_rms | 2.219 | 1.529 | +0.69 |
| stand_action_change | 0.368 | 0.1416 | +0.226 |
| stand_pelvis_speed | 1.035 | 0.44 | +0.595 |
| stand_torso_angvel | 1.353 | 0.766 | +0.587 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 17 of 53 measurements beyond tolerance

- 3.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 52 deg (signed +52), step 49: robot +1.39 vs ref -0.17 rad
- 3.4 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 50 deg (signed +50), step 52: robot +0.70 vs ref -0.69 rad
- 3.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.26 m, max 0.43 m
- 2.3 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 35 deg (signed +16), step 10: robot -1.18 vs ref -0.14 rad
- 2.1 asymmetry:elbow - left/right differ 27 deg vs reference 5 deg
- 2.0 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 30 deg (signed -30), step 29: robot +0.29 vs ref +1.26 rad

**crouch**: 18 of 53 measurements beyond tolerance

- 3.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 56 deg (signed +56), step 90: robot +1.05 vs ref -0.18 rad
- 2.2 body:ankle_roll - left_ankle_roll_link: mean 0.18 m, max 0.32 m
- 2.0 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 30 deg (signed +30), step 71: robot +0.82 vs ref -0.03 rad
- 1.7 joint:elbow - right_elbow_joint: mean |err| 25 deg (signed -25), step 90: robot -0.11 vs ref +1.13 rad
- 1.6 joint:waist_pitch - waist_pitch_joint: mean |err| 24 deg (signed -11), step 77: robot -0.19 vs ref +0.52 rad
- 1.6 asymmetry:hip_yaw - left/right differ 24 deg vs reference 8 deg

**takeoff**: 22 of 51 measurements beyond tolerance

- 5.4 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 81 deg (signed +81), step 95: robot +1.09 vs ref -0.37 rad
- 4.1 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 61 deg (signed -61), step 97: robot -0.16 vs ref +1.07 rad
- 3.7 body:wrist_yaw - left_wrist_yaw_link: mean 0.30 m, max 0.40 m
- 3.6 asymmetry:hip_yaw - left/right differ 47 deg vs reference 11 deg
- 3.4 body:ankle_roll - left_ankle_roll_link: mean 0.28 m, max 0.34 m
- 3.1 joint:elbow - right_elbow_joint: mean |err| 46 deg (signed -46), step 91: robot -0.33 vs ref +0.95 rad

**flight**: 18 of 51 measurements beyond tolerance

- 4.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 70 deg (signed +70), step 106: robot +0.99 vs ref -0.45 rad
- 4.6 asymmetry:wrist_roll - left/right differ 52 deg vs reference 6 deg
- 3.3 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 49 deg (signed +49), step 109: robot +0.11 vs ref -1.20 rad
- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.25 m, max 0.40 m
- 2.9 body:wrist_yaw - left_wrist_yaw_link: mean 0.23 m, max 0.48 m
- 2.3 body:knee - left_knee_link: mean 0.18 m, max 0.28 m

**land**: 16 of 53 measurements beyond tolerance

- 2.8 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 43 deg (signed -43), step 123: robot -1.82 vs ref -0.78 rad
- 2.6 jitter:waist_roll - waist_roll_joint: joint acceleration RMS 66 vs reference 4 rad/s^2
- 2.4 body:wrist_yaw - right_wrist_yaw_link: mean 0.19 m, max 0.23 m
- 2.2 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 33 deg (signed -33), step 126: robot -0.11 vs ref +0.54 rad
- 2.2 jitter:elbow - left_elbow_joint: joint acceleration RMS 233 vs reference 30 rad/s^2
- 1.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 27 deg (signed +27), step 121: robot +0.39 vs ref -0.32 rad

**settle**: 14 of 54 measurements beyond tolerance

- 3.6 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 62 vs reference 1 rad/s^2
- 3.1 jitter:all - mean action change 0.157 (quiet < 0.05)
- 2.7 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 56 vs reference 2 rad/s^2
- 2.1 jitter:knee - right_knee_joint: joint acceleration RMS 53 vs reference 3 rad/s^2
- 1.8 jitter:waist_pitch - waist_pitch_joint: joint acceleration RMS 36 vs reference 2 rad/s^2
- 1.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 27 deg (signed +27), step 154: robot +0.78 vs ref -0.13 rad

**stand_after**: 37 of 54 measurements beyond tolerance

- 17.4 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 261 vs reference 0 rad/s^2
- 14.7 jitter:knee - left_knee_joint: joint acceleration RMS 220 vs reference 0 rad/s^2
- 12.9 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 194 vs reference 0 rad/s^2
- 12.9 jitter:hip_yaw - left_hip_yaw_joint: joint acceleration RMS 193 vs reference 0 rad/s^2
- 8.8 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 132 vs reference 0 rad/s^2
- 8.7 jitter:all - mean action change 0.433 (quiet < 0.05)

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.4 | joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.289 |
| 2.3 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.133 |
| 1.2 | joint:shoulder_roll:stand | dyn_joint | 0.0 | 0.3 | 0.365 |
| 2.0 | joint:shoulder_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.173 |
| 3.4 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.0536 |
| 2.1 | asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.154 |
| 2.0 | contact:left_foot:stand | dyn_contact | 2.0 | None | - |
| 1.7 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.231 |
| 1.2 | joint:hip_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.36 |
| 1.3 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.327 |
| 1.0 | joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.409 |
| 1.2 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.345 |
| 2.2 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.17 |
| 1.5 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.301 |
| 1.2 | body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.376 |
| 1.6 | asymmetry:hip_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.255 |
| 1.3 | asymmetry:shoulder_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.322 |
| 2.5 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.118 |
| 3.1 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0687 |
| 1.3 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.315 |
| 1.1 | joint:knee:takeoff | dyn_joint | 0.0 | 0.3 | 0.384 |
| 3.4 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.0639 |
| 3.7 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0507 |
| 2.2 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.169 |
| 1.3 | asymmetry:shoulder_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.322 |
| 1.5 | asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.268 |
| 1.0 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.406 |
| 1.9 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.186 |
| 1.3 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.327 |
| 1.8 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.21 |
| 1.2 | joint:waist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.339 |
| 1.8 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.214 |
| 3.3 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.0566 |
| 3.2 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.603 |
| 2.9 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.102 |
| 2.3 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.162 |
| 1.4 | asymmetry:shoulder_pitch:flight | dyn_sym | 0.0 | 0.2 | 0.3 |
| 4.6 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.0174 |
| 1.2 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.372 |
| 2.4 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.144 |
| 1.7 | asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.223 |
| 3.1 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.1 | asymmetry:hip_pitch:stand_after | dyn_sym | 0.0 | 0.2 | 0.397 |
| 1.6 | asymmetry:hip_roll:stand_after | dyn_sym | 1.0 | 0.3 | 0.398 |
| 3.1 | asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.068 |
| 1.2 | asymmetry:knee:stand_after | dyn_sym | 0.0 | 0.2 | 0.36 |
| 2.3 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.139 |
| 4.4 | asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.0215 |
| 1.3 | asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.322 |
| 1.3 | contact:left_foot:stand_after | dyn_contact | 2.0 | None | - |
| 8.7 | jitter:all:stand_after | dyn_quiet | 2.0 | 1.0 | - |
| 3.6 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.1 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0281 |
| 2.7 | jitter:hip_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.8 | joint:elbow:stand_after | dyn_joint | 0.0 | 0.3 | 0.203 |
| 2.6 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.106 |
| 17.4 | jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 14.7 | jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.9 | jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.0 | jitter:shoulder_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.9 | jitter:ankle_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.1 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 8.8 | jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.4 | joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.00895 |
| 5.3 | joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.00978 |
| 7.2 | jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.4 | joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.307 |
| 3.6 | asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.0432 |
| 7.3 | jitter:shoulder_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 6.1 | jitter:hip_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.7 | jitter:elbow:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.6 | joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0173 |
| 4.4 | jitter:waist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.3 | jitter:waist_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |

74 of 162 library checks fail.

## D. Deviations no check covers yet (severity > 2): 17

- 4.2 jitter:wrist_pitch:stand_after - left_wrist_pitch_joint: joint acceleration RMS 63 vs reference 0 rad/s^2
- 3.8 joint:wrist_pitch:crouch - right_wrist_pitch_joint: mean |err| 56 deg (signed +56), step 90: robot +1.05 vs ref -0.18 rad
- 3.5 joint:wrist_pitch:stand - right_wrist_pitch_joint: mean |err| 52 deg (signed +52), step 49: robot +1.39 vs ref -0.17 rad
- 3.3 jitter:shoulder_roll:stand_after - right_shoulder_roll_joint: joint acceleration RMS 50 vs reference 0 rad/s^2
- 3.3 body:wrist_yaw:stand - left_wrist_yaw_link: mean 0.26 m, max 0.43 m
- 3.2 body:wrist_yaw:stand_after - right_wrist_yaw_link: mean 0.26 m, max 0.30 m
- 3.0 joint:shoulder_pitch:stand_after - right_shoulder_pitch_joint: mean |err| 45 deg (signed -45), step 178: robot -1.17 vs ref -0.15 rad
- 2.8 joint:shoulder_pitch:land - right_shoulder_pitch_joint: mean |err| 43 deg (signed -43), step 123: robot -1.82 vs ref -0.78 rad
- 2.8 joint:wrist_yaw:takeoff - left_wrist_yaw_joint: mean |err| 42 deg (signed +42), step 94: robot +1.01 vs ref +0.25 rad
- 2.6 jitter:waist_roll:land - waist_roll_joint: joint acceleration RMS 66 vs reference 4 rad/s^2
- 2.5 body:ankle_roll:stand_after - right_ankle_roll_link: mean 0.20 m, max 0.28 m
- 2.5 jitter:waist_pitch:stand_after - waist_pitch_joint: joint acceleration RMS 37 vs reference 0 rad/s^2
- 2.4 joint:hip_yaw:stand_after - right_hip_yaw_joint: mean |err| 35 deg (signed +35), step 166: robot +0.68 vs ref -0.20 rad
- 2.2 joint:shoulder_yaw:land - right_shoulder_yaw_joint: mean |err| 33 deg (signed -33), step 126: robot -0.11 vs ref +0.54 rad
- 2.2 jitter:elbow:land - left_elbow_joint: joint acceleration RMS 233 vs reference 30 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.27| rad (end +0.22), reference max |0.10|
- arm joints mean |err| 16 deg; worst: left_shoulder_pitch 28, right_shoulder_pitch 27, right_elbow 20, left_shoulder_roll 16
- action change mean 0.317 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 115, left_hip_yaw 103, left_knee 98, left_ankle_roll 86
- feet off the floor (> 6 cm): left 4, right 0 of 58 steps
- land (steps 121-129): pelvis speed mean 0.43 m/s, last 0.25; drift 0.06 m
- settle (steps 130-154): pelvis speed mean 0.32 m/s, last 0.58; drift 0.11 m
- stand_after (steps 155-187): pelvis speed mean 1.19 m/s, last 1.97; drift 0.77 m

## F. Training-config audit (what the training actually ran)

- 44 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 4

## F2. Knobs this round trained with vs round 10 (1 differences)

- terms.term_stand_fail.max_tilt: 30.0 -> 25.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r10: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7d0575f2bba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r11: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x78131a71fba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] flip terminations: r10: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 30.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
  r11: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- [train_dance] library fixes: r10: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya
  r11: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
