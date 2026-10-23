# Round 9 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_03-07-12_flipauto_r09`, best checkpoint `model_6999.pt` (score 9.248), evaluated: model_6000.pt 7.357, model_6500.pt 7.334, model_6999.pt 9.248

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.248 | 9.097 | +0.151 |
| robot_rotation_deg | 358.3 | 344.2 | +14.1 |
| robot_max_rotation_deg | 367.2 | 370.8 | -3.6 |
| robot_peak_pelvis_m | 1.194 | 1.341 | -0.147 |
| pelvis_rise_m | 0.436 | 0.574 | -0.138 |
| robot_airborne_s | 0.58 | 0.74 | -0.16 |
| landed_upright | True | True |  |
| end_tilt_deg | 13.2 | 10.2 | +3 |
| early_fall | False | False |  |
| plane_dev_max_deg | 17.0 | 18.5 | -1.5 |
| plane_dev_mean_deg | 7.7 | 7.6 | +0.1 |
| leg_asym_deg | 3.0 | 4.7 | -1.7 |
| leg_err_deg | 6.4 | 19.6 | -13.2 |
| feet_dist_max_m | 0.228 | 0.322 | -0.094 |
| feet_dist_touchdown_m | 0.201 | 0.241 | -0.04 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 67 | 22 | +45 |
| flight_hip_err_rad | -0.2 | 0.52 | -0.72 |
| rot_at_ref_landing_deg | 323.0 | 285.4 | +37.6 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.747 | 0.705 | +0.042 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.209 | 0.313 | -0.104 |
| flight_hip_mean_rad | -1.74 | -1.03 | -0.71 |
| flight_knee_max_rad | 1.69 | 2.95 | -1.26 |
| flight_knee_overfold_rad | 0.35 | 2.06 | -1.71 |
| knee_sep_min_m | 0.192 | 0.202 | -0.01 |
| track_body_err_m | 0.1202 | 0.1444 | -0.0242 |
| track_joint_err | 2.3686 | 2.3985 | -0.0299 |
| knee_sep_max_m | 0.312 | 0.369 | -0.057 |
| flight_hip_roll_max_rad | 0.27 | 0.28 | -0.01 |
| flight_hip_yaw_max_rad | 0.26 | 0.44 | -0.18 |
| stand_arm_vel_rms | 2.962 | - |  |
| stand_action_change | 0.4655 | - |  |
| stand_pelvis_speed | 1.2 | - |  |
| stand_torso_angvel | 1.805 | - |  |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 28 of 53 measurements beyond tolerance

- 13.7 contact:left_foot - left_foot off the floor for 41 of 71 steps
- 7.7 contact:right_foot - right_foot off the floor for 23 of 71 steps
- 4.6 body:wrist_yaw - left_wrist_yaw_link: mean 0.37 m, max 0.58 m
- 3.8 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 57 deg (signed +5), step 10: robot -2.14 vs ref -0.10 rad
- 3.6 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 325 vs reference 25 rad/s^2
- 3.0 asymmetry:shoulder_pitch - left/right differ 42 deg vs reference 11 deg

**crouch**: 19 of 53 measurements beyond tolerance

- 2.8 joint:wrist_roll - left_wrist_roll_joint: mean |err| 41 deg (signed +41), step 89: robot +0.55 vs ref -0.41 rad
- 2.3 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 34 deg (signed +34), step 82: robot +0.60 vs ref -0.21 rad
- 1.8 body:ankle_roll - right_ankle_roll_link: mean 0.14 m, max 0.19 m
- 1.7 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 124 vs reference 20 rad/s^2
- 1.6 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 23 deg (signed +23), step 90: robot +0.79 vs ref +0.20 rad
- 1.5 joint:waist_pitch - waist_pitch_joint: mean |err| 22 deg (signed -9), step 79: robot -0.11 vs ref +0.52 rad

**takeoff**: 25 of 51 measurements beyond tolerance

- 5.2 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 78 deg (signed +78), step 94: robot +0.37 vs ref -1.15 rad
- 4.5 body:wrist_yaw - right_wrist_yaw_link: mean 0.36 m, max 0.45 m
- 3.9 asymmetry:hip_yaw - left/right differ 51 deg vs reference 11 deg
- 3.8 joint:elbow - right_elbow_joint: mean |err| 58 deg (signed -58), step 91: robot -0.59 vs ref +0.95 rad
- 3.0 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 46 deg (signed +46), step 97: robot +0.51 vs ref -0.38 rad
- 2.9 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 44 deg (signed +44), step 97: robot +1.24 vs ref +0.37 rad

**flight**: 17 of 51 measurements beyond tolerance

- 3.4 body:wrist_yaw - right_wrist_yaw_link: mean 0.27 m, max 0.44 m
- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.26 m, max 0.47 m
- 2.8 joint:elbow - right_elbow_joint: mean |err| 41 deg (signed +39), step 120: robot +0.98 vs ref -0.42 rad
- 2.7 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 41 deg (signed +41), step 106: robot +0.50 vs ref -0.45 rad
- 2.3 body:knee - left_knee_link: mean 0.18 m, max 0.30 m
- 2.0 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 30 deg (signed +30), step 109: robot -0.21 vs ref -1.20 rad

**land**: 21 of 53 measurements beyond tolerance

- 3.8 jitter:waist_roll - waist_roll_joint: joint acceleration RMS 98 vs reference 4 rad/s^2
- 3.6 joint:elbow - right_elbow_joint: mean |err| 54 deg (signed +54), step 121: robot +1.04 vs ref -0.44 rad
- 3.4 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 50 deg (signed -50), step 124: robot -1.88 vs ref -0.74 rad
- 3.1 asymmetry:elbow - left/right differ 32 deg vs reference 1 deg
- 2.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.19 m, max 0.22 m
- 2.1 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 202 vs reference 27 rad/s^2

**settle**: 31 of 54 measurements beyond tolerance

- 12.2 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 248 vs reference 2 rad/s^2
- 7.4 jitter:knee - left_knee_joint: joint acceleration RMS 164 vs reference 2 rad/s^2
- 7.3 jitter:hip_yaw - left_hip_yaw_joint: joint acceleration RMS 134 vs reference 1 rad/s^2
- 7.2 jitter:all - mean action change 0.359 (quiet < 0.05)
- 6.0 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 127 vs reference 2 rad/s^2
- 4.9 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 100 vs reference 2 rad/s^2

**stand_after**: 39 of 54 measurements beyond tolerance

- 21.6 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 324 vs reference 0 rad/s^2
- 12.9 jitter:knee - left_knee_joint: joint acceleration RMS 194 vs reference 0 rad/s^2
- 10.7 jitter:hip_yaw - left_hip_yaw_joint: joint acceleration RMS 160 vs reference 0 rad/s^2
- 9.0 jitter:all - mean action change 0.449 (quiet < 0.05)
- 8.7 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 130 vs reference 0 rad/s^2
- 7.8 jitter:ankle_roll - right_ankle_roll_joint: joint acceleration RMS 116 vs reference 0 rad/s^2

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.6 | joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.242 |
| 3.8 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.0367 |
| 1.3 | joint:shoulder_roll:stand | dyn_joint | 0.0 | 0.3 | 0.334 |
| 2.4 | joint:shoulder_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.123 |
| 2.6 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.108 |
| 1.3 | asymmetry:hip_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.32 |
| 1.1 | asymmetry:shoulder_roll:stand | dyn_sym | 0.0 | 0.2 | 0.379 |
| 1.1 | asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.388 |
| 1.4 | asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.287 |
| 13.7 | contact:left_foot:stand | dyn_contact | 0.0 | None | - |
| 7.7 | contact:right_foot:stand | dyn_contact | 0.0 | None | - |
| 1.4 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.291 |
| 1.1 | joint:hip_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.381 |
| 1.2 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.366 |
| 1.0 | joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.406 |
| 2.8 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.0906 |
| 1.8 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.24 |
| 1.4 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.323 |
| 1.2 | body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.392 |
| 1.1 | asymmetry:hip_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.373 |
| 2.4 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.124 |
| 3.8 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.035 |
| 2.0 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.178 |
| 2.4 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.144 |
| 4.5 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0272 |
| 1.9 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.215 |
| 1.1 | asymmetry:hip_pitch:takeoff | dyn_sym | 0.0 | 0.2 | 0.397 |
| 1.2 | asymmetry:hip_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.365 |
| 1.3 | asymmetry:knee:takeoff | dyn_sym | 0.0 | 0.2 | 0.33 |
| 2.8 | asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.0886 |
| 2.8 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.0907 |
| 1.5 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.266 |
| 1.5 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.261 |
| 1.6 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.254 |
| 1.7 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.22 |
| 2.0 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.174 |
| 3.2 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.595 |
| 3.4 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0669 |
| 2.3 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.161 |
| 1.3 | asymmetry:elbow:flight | dyn_sym | 0.0 | 0.2 | 0.317 |
| 1.3 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.32 |
| 1.2 | joint:knee:land | dyn_joint | 0.0 | 0.3 | 0.357 |
| 1.6 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.28 |
| 2.3 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.157 |
| 1.9 | asymmetry:shoulder_pitch:land | dyn_sym | 0.0 | 0.2 | 0.19 |
| 1.1 | asymmetry:shoulder_roll:land | dyn_sym | 0.0 | 0.2 | 0.393 |
| 3.1 | asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.067 |
| 1.1 | joint:elbow:settle | dyn_joint | 0.0 | 0.3 | 0.396 |
| 1.5 | joint:shoulder_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.279 |
| 2.3 | joint:wrist_roll:settle | dyn_joint | 0.0 | 0.3 | 0.134 |
| 2.0 | asymmetry:shoulder_pitch:settle | dyn_sym | 0.0 | 0.2 | 0.171 |
| 1.3 | asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.333 |
| 1.5 | asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.281 |
| 1.3 | contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 7.2 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.3 | asymmetry:knee:stand_after | dyn_sym | 0.0 | 0.2 | 0.31 |
| 1.1 | asymmetry:ankle_pitch:stand_after | dyn_sym | 0.0 | 0.2 | 0.372 |
| 3.9 | asymmetry:shoulder_pitch:stand_after | dyn_sym | 0.0 | 0.2 | 0.0338 |
| 4.8 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0151 |
| 2.1 | asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.155 |
| 7.0 | contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 4.0 | contact:right_foot:stand_after | dyn_contact | 0.0 | None | - |
| 9.0 | jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.2 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 5.2 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0108 |
| 7.3 | jitter:hip_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 2.2 | joint:elbow:stand_after | dyn_joint | 0.0 | 0.3 | 0.151 |
| 2.0 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.178 |
| 21.6 | jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.9 | jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 10.7 | jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 8.7 | jitter:shoulder_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 7.8 | jitter:ankle_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 7.4 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |

74 of 150 library checks fail.

## D. Deviations no check covers yet (severity > 2): 48

- 7.4 jitter:elbow:stand_after - right_elbow_joint: joint acceleration RMS 111 vs reference 0 rad/s^2
- 6.3 jitter:wrist_roll:stand_after - right_wrist_roll_joint: joint acceleration RMS 94 vs reference 0 rad/s^2
- 6.0 jitter:shoulder_yaw:settle - left_shoulder_yaw_joint: joint acceleration RMS 127 vs reference 2 rad/s^2
- 5.6 jitter:hip_roll:stand_after - left_hip_roll_joint: joint acceleration RMS 84 vs reference 0 rad/s^2
- 5.6 jitter:shoulder_pitch:stand_after - left_shoulder_pitch_joint: joint acceleration RMS 84 vs reference 0 rad/s^2
- 5.3 jitter:shoulder_roll:stand_after - left_shoulder_roll_joint: joint acceleration RMS 80 vs reference 0 rad/s^2
- 5.3 jitter:hip_pitch:stand_after - left_hip_pitch_joint: joint acceleration RMS 79 vs reference 0 rad/s^2
- 4.9 jitter:ankle_roll:settle - left_ankle_roll_joint: joint acceleration RMS 100 vs reference 2 rad/s^2
- 4.7 joint:shoulder_pitch:stand_after - right_shoulder_pitch_joint: mean |err| 71 deg (signed -71), step 181: robot -1.54 vs ref -0.15 rad
- 4.6 body:wrist_yaw:stand - left_wrist_yaw_link: mean 0.37 m, max 0.58 m
- 4.5 jitter:waist_yaw:stand_after - waist_yaw_joint: joint acceleration RMS 67 vs reference 0 rad/s^2
- 4.5 joint:wrist_yaw:stand_after - left_wrist_yaw_joint: mean |err| 67 deg (signed +67), step 181: robot +1.26 vs ref -0.17 rad
- 4.5 joint:shoulder_roll:stand_after - left_shoulder_roll_joint: mean |err| 67 deg (signed +67), step 180: robot +1.80 vs ref +0.33 rad
- 4.1 body:wrist_yaw:stand_after - right_wrist_yaw_link: mean 0.33 m, max 0.36 m
- 3.9 asymmetry:hip_yaw:takeoff - left/right differ 51 deg vs reference 11 deg

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.26| rad (end +0.07), reference max |0.10|
- arm joints mean |err| 24 deg; worst: right_shoulder_pitch 50, left_shoulder_roll 48, left_elbow 25, left_shoulder_pitch 21
- action change mean 0.413 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 220, right_ankle_pitch 171, left_knee 128, left_shoulder_yaw 106
- feet off the floor (> 6 cm): left 25, right 12 of 58 steps

## F. Training-config audit (what the training actually ran)

- 38 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 30.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 8, decider terms: 3

## F2. Knobs this round trained with vs round 8 (4 differences)

- extra_dyn: - -> [{"name": "agent_r09_hip_tuck", "func": "dyn_joint", "weight": 3.0, "params": {"joints": ["left_hip_pitch_joint", "right
- weights.flip_stand_quiet: - -> 3.0
- weights.flip_stand_still: - -> 3.0
- weights.flip_stay_down: 10.0 -> 5.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r8: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7070dc18b9c0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r9: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x75c968007ba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] fidelity curriculum: r8: tracking weights x1.5, std x0.85
  r9: tracking weights x2.25, std x0.722
- [train_dance] flip rewards x2.0: r8: {'flip_pushoff': 4.0, 'flip_lean': 3.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 6.75, 'flip_plane_axis': 6.75, 'flip_plane_rate': 4.5, 'flip_leg_sym': 12.0, 'flip_leg_track': 12.0, 'flip_leg_calm': 6.0, 'flip_feet_together': 12
  r9: {'flip_pushoff': 4.0, 'flip_lean': 3.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 6.75, 'flip_plane_axis': 6.75, 'flip_plane_rate': 4.5, 'flip_leg_sym': 12.0, 'flip_leg_track': 12.0, 'flip_leg_calm': 6.0, 'flip_feet_together': 12
- [train_dance] library fixes: r8: -
  r9: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_yaw_flight', 1.0), ('lib_jitter_all_settle', 1.0), ('lib_asymmetry_hip_roll_sta

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
