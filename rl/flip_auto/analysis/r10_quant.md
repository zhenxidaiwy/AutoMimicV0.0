# Round 10 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_04-30-18_flipauto_r10`, best checkpoint `model_8000.pt` (score 7.414), evaluated: model_7500.pt 7.409, model_8000.pt 7.414, model_8498.pt 7.377

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 7.414 | 9.248 | -1.83 |
| robot_rotation_deg | 353.2 | 358.3 | -5.1 |
| robot_max_rotation_deg | 361.2 | 367.2 | -6 |
| robot_peak_pelvis_m | 1.167 | 1.194 | -0.027 |
| pelvis_rise_m | 0.389 | 0.436 | -0.047 |
| robot_airborne_s | 0.58 | 0.58 | +0 |
| landed_upright | True | True |  |
| end_tilt_deg | 18.3 | 13.2 | +5.1 |
| early_fall | False | False |  |
| plane_dev_max_deg | 9.1 | 17.0 | -7.9 |
| plane_dev_mean_deg | 4.8 | 7.7 | -2.9 |
| leg_asym_deg | 1.9 | 3.0 | -1.1 |
| leg_err_deg | 5.1 | 6.4 | -1.3 |
| feet_dist_max_m | 0.232 | 0.228 | +0.004 |
| feet_dist_touchdown_m | 0.203 | 0.201 | +0.002 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 1 | 67 | -66 |
| flight_hip_err_rad | -0.11 | -0.2 | +0.09 |
| rot_at_ref_landing_deg | 320.5 | 323.0 | -2.5 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.738 | 0.747 | -0.009 |
| stand_stable | False | True |  |
| stand_feet_d_end | 0.349 | 0.209 | +0.14 |
| flight_hip_mean_rad | -1.65 | -1.74 | +0.09 |
| flight_knee_max_rad | 1.67 | 1.69 | -0.02 |
| flight_knee_overfold_rad | 0.32 | 0.35 | -0.03 |
| knee_sep_min_m | 0.182 | 0.192 | -0.01 |
| track_body_err_m | 0.104 | 0.1202 | -0.0162 |
| track_joint_err | 2.1392 | 2.3686 | -0.229 |
| knee_sep_max_m | 0.279 | 0.312 | -0.033 |
| flight_hip_roll_max_rad | 0.1 | 0.27 | -0.17 |
| flight_hip_yaw_max_rad | 0.25 | 0.26 | -0.01 |
| stand_arm_vel_rms | 1.529 | 2.962 | -1.43 |
| stand_action_change | 0.1416 | 0.4655 | -0.324 |
| stand_pelvis_speed | 0.44 | 1.2 | -0.76 |
| stand_torso_angvel | 0.766 | 1.805 | -1.04 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 15 of 53 measurements beyond tolerance

- 3.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.27 m, max 0.41 m
- 2.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 43 deg (signed +42), step 39: robot +0.88 vs ref -0.25 rad
- 2.8 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 42 deg (signed +36), step 52: robot +0.92 vs ref -0.69 rad
- 2.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 39 deg (signed +11), step 50: robot -1.55 vs ref -2.69 rad
- 2.4 joint:wrist_roll - left_wrist_roll_joint: mean |err| 36 deg (signed +36), step 38: robot +0.85 vs ref -0.21 rad
- 2.4 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 35 deg (signed -35), step 30: robot +0.24 vs ref +1.34 rad

**crouch**: 17 of 53 measurements beyond tolerance

- 3.1 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 46 deg (signed +46), step 90: robot +0.87 vs ref -0.18 rad
- 2.0 joint:wrist_roll - left_wrist_roll_joint: mean |err| 30 deg (signed +30), step 74: robot +0.79 vs ref +0.09 rad
- 1.8 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 28 deg (signed +28), step 90: robot +0.94 vs ref +0.20 rad
- 1.8 body:ankle_roll - right_ankle_roll_link: mean 0.14 m, max 0.24 m
- 1.7 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 25 deg (signed +25), step 89: robot -1.05 vs ref -1.74 rad
- 1.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.11 m, max 0.19 m

**takeoff**: 24 of 51 measurements beyond tolerance

- 4.7 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 70 deg (signed +70), step 95: robot +0.89 vs ref -0.37 rad
- 4.3 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 65 deg (signed +65), step 94: robot +0.11 vs ref -1.15 rad
- 4.0 body:wrist_yaw - left_wrist_yaw_link: mean 0.32 m, max 0.43 m
- 3.6 asymmetry:hip_yaw - left/right differ 48 deg vs reference 11 deg
- 3.0 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 45 deg (signed +45), step 93: robot +1.06 vs ref +0.23 rad
- 2.7 body:ankle_roll - right_ankle_roll_link: mean 0.22 m, max 0.25 m

**flight**: 18 of 51 measurements beyond tolerance

- 4.0 asymmetry:wrist_roll - left/right differ 46 deg vs reference 6 deg
- 3.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 53 deg (signed +53), step 98: robot +0.81 vs ref -0.37 rad
- 3.5 body:wrist_yaw - right_wrist_yaw_link: mean 0.28 m, max 0.50 m
- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.26 m, max 0.45 m
- 2.9 joint:wrist_roll - left_wrist_roll_joint: mean |err| 44 deg (signed -39), step 107: robot -0.82 vs ref +0.70 rad
- 2.5 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 38 deg (signed +38), step 109: robot -0.10 vs ref -1.20 rad

**land**: 13 of 53 measurements beyond tolerance

- 2.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 40 deg (signed -40), step 123: robot -1.81 vs ref -0.82 rad
- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.20 m
- 1.9 joint:elbow - right_elbow_joint: mean |err| 28 deg (signed +28), step 122: robot +0.33 vs ref -0.43 rad
- 1.8 jitter:shoulder_yaw - right_shoulder_yaw_joint: joint acceleration RMS 100 vs reference 13 rad/s^2
- 1.8 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 27 deg (signed -27), step 125: robot -0.02 vs ref +0.55 rad
- 1.8 jitter:elbow - left_elbow_joint: joint acceleration RMS 186 vs reference 30 rad/s^2

**settle**: 6 of 54 measurements beyond tolerance

- 2.2 jitter:all - mean action change 0.108 (quiet < 0.05)
- 1.5 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 22 deg (signed +22), step 154: robot +0.61 vs ref -0.17 rad
- 1.4 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 21 deg (signed +21), step 154: robot +0.59 vs ref -0.13 rad
- 1.4 asymmetry:elbow - left/right differ 17 deg vs reference 3 deg
- 1.1 jitter:knee - left_knee_joint: joint acceleration RMS 25 vs reference 2 rad/s^2
- 1.1 jitter:waist_pitch - waist_pitch_joint: joint acceleration RMS 21 vs reference 2 rad/s^2

**stand_after**: 33 of 54 measurements beyond tolerance

- 7.6 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 115 vs reference 0 rad/s^2
- 6.5 jitter:knee - left_knee_joint: joint acceleration RMS 97 vs reference 0 rad/s^2
- 4.8 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 72 vs reference 0 rad/s^2
- 4.3 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 65 deg (signed +65), step 187: robot +1.21 vs ref -0.13 rad
- 4.2 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 64 vs reference 0 rad/s^2
- 4.2 asymmetry:shoulder_roll - left/right differ 43 deg vs reference 0 deg

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.6 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.106 |
| 1.0 | joint:shoulder_roll:stand | dyn_joint | 0.0 | 0.3 | 0.406 |
| 2.4 | joint:shoulder_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.128 |
| 2.8 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.0867 |
| 1.1 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.379 |
| 1.7 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.228 |
| 1.3 | joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.329 |
| 2.0 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.172 |
| 1.8 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.245 |
| 1.4 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.319 |
| 1.3 | body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.356 |
| 1.0 | asymmetry:hip_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.407 |
| 1.3 | asymmetry:shoulder_pitch:crouch | dyn_sym | 0.0 | 0.2 | 0.33 |
| 2.1 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.156 |
| 2.6 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.103 |
| 1.5 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.26 |
| 2.7 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.113 |
| 4.0 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0399 |
| 2.1 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.194 |
| 1.0 | asymmetry:hip_pitch:takeoff | dyn_sym | 0.0 | 0.2 | 0.404 |
| 1.1 | asymmetry:knee:takeoff | dyn_sym | 0.0 | 0.2 | 0.388 |
| 2.6 | asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.107 |
| 1.6 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.247 |
| 1.6 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.246 |
| 1.8 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.217 |
| 2.0 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.18 |
| 1.1 | joint:waist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.399 |
| 2.9 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.079 |
| 2.5 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.11 |
| 3.2 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.596 |
| 3.5 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0599 |
| 2.2 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.175 |
| 1.7 | asymmetry:shoulder_pitch:flight | dyn_sym | 0.0 | 0.2 | 0.224 |
| 4.0 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.0313 |
| 2.0 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.196 |
| 1.5 | asymmetry:shoulder_pitch:land | dyn_sym | 0.0 | 0.2 | 0.268 |
| 1.4 | asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.305 |
| 2.2 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 3.2 | asymmetry:shoulder_pitch:stand_after | dyn_sym | 0.0 | 0.2 | 0.0599 |
| 4.2 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0254 |
| 1.5 | asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.261 |
| 2.9 | jitter:all:stand_after | dyn_quiet | 2.0 | 1.0 | - |
| 1.0 | joint:waist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.416 |
| 4.3 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0229 |
| 2.3 | joint:elbow:stand_after | dyn_joint | 0.0 | 0.3 | 0.139 |
| 2.1 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.155 |
| 7.6 | jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 6.5 | jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.3 | jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | jitter:shoulder_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.2 | jitter:ankle_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.8 | jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.7 | joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.0168 |
| 4.3 | joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0232 |
| 4.0 | jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 3.7 | joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.0411 |
| 3.6 | asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.0415 |

58 of 156 library checks fail.

## D. Deviations no check covers yet (severity > 2): 18

- 3.5 joint:wrist_pitch:flight - right_wrist_pitch_joint: mean |err| 53 deg (signed +53), step 98: robot +0.81 vs ref -0.37 rad
- 3.4 body:wrist_yaw:stand - left_wrist_yaw_link: mean 0.27 m, max 0.41 m
- 3.1 joint:wrist_pitch:crouch - right_wrist_pitch_joint: mean |err| 46 deg (signed +46), step 90: robot +0.87 vs ref -0.18 rad
- 3.1 body:wrist_yaw:stand_after - right_wrist_yaw_link: mean 0.25 m, max 0.27 m
- 3.0 joint:wrist_yaw:takeoff - left_wrist_yaw_joint: mean |err| 45 deg (signed +45), step 93: robot +1.06 vs ref +0.23 rad
- 2.8 joint:wrist_pitch:stand - right_wrist_pitch_joint: mean |err| 43 deg (signed +42), step 39: robot +0.88 vs ref -0.25 rad
- 2.7 jitter:waist_pitch:stand_after - waist_pitch_joint: joint acceleration RMS 41 vs reference 0 rad/s^2
- 2.6 joint:shoulder_pitch:stand_after - right_shoulder_pitch_joint: mean |err| 40 deg (signed -40), step 186: robot -1.21 vs ref -0.15 rad
- 2.6 joint:shoulder_pitch:land - left_shoulder_pitch_joint: mean |err| 40 deg (signed -40), step 123: robot -1.81 vs ref -0.82 rad
- 2.6 joint:shoulder_roll:stand_after - right_shoulder_roll_joint: mean |err| 39 deg (signed -39), step 165: robot -1.22 vs ref -0.34 rad
- 2.5 joint:knee:stand_after - left_knee_joint: mean |err| 38 deg (signed +38), step 177: robot +0.83 vs ref +0.06 rad
- 2.5 body:knee:stand_after - left_knee_link: mean 0.20 m, max 0.24 m
- 2.4 joint:wrist_roll:takeoff - right_wrist_roll_joint: mean |err| 36 deg (signed -36), step 97: robot -0.59 vs ref +0.07 rad
- 2.4 joint:wrist_roll:stand - left_wrist_roll_joint: mean |err| 36 deg (signed +36), step 38: robot +0.85 vs ref -0.21 rad
- 2.2 jitter:elbow:stand_after - left_elbow_joint: joint acceleration RMS 32 vs reference 0 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.38| rad (end +0.31), reference max |0.10|
- arm joints mean |err| 16 deg; worst: right_elbow 26, right_shoulder_pitch 25, right_shoulder_roll 24, left_elbow 21
- action change mean 0.127 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 37, left_knee 34, right_wrist_roll 30, left_elbow 26
- feet off the floor (> 6 cm): left 0, right 0 of 58 steps

## F. Training-config audit (what the training actually ran)

- 43 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 30.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 3

## F2. Knobs this round trained with vs round 9 (3 differences)

- tracking.scale: 2.25 -> 1.5
- tracking.std_scale: 0.722 -> 0.85
- weights.flip_stand_still: 3.0 -> 4.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r9: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x75c968007ba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r10: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7d0575f2bba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] fidelity curriculum: r9: tracking weights x2.25, std x0.722
  r10: tracking weights x1.5, std x0.85
- [train_dance] flip rewards x2.0: r9: {'flip_pushoff': 4.0, 'flip_lean': 3.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 6.75, 'flip_plane_axis': 6.75, 'flip_plane_rate': 4.5, 'flip_leg_sym': 12.0, 'flip_leg_track': 12.0, 'flip_leg_calm': 6.0, 'flip_feet_together': 12
  r10: {'flip_pushoff': 4.0, 'flip_lean': 3.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 6.75, 'flip_plane_axis': 6.75, 'flip_plane_rate': 4.5, 'flip_leg_sym': 12.0, 'flip_leg_track': 12.0, 'flip_leg_calm': 6.0, 'flip_feet_together': 12
- [train_dance] library fixes: r9: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_yaw_flight', 1.0), ('lib_jitter_all_settle', 1.0), ('lib_asymmetry_hip_roll_sta
  r10: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
