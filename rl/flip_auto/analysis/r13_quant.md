# Round 13 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_08-45-13_flipauto_r13`, best checkpoint `model_11499.pt` (score 9.55), evaluated: model_10500.pt 9.493, model_11000.pt 9.502, model_11499.pt 9.55

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.55 | 9.519 | +0.031 |
| robot_rotation_deg | 366.9 | 367.9 | -1 |
| robot_max_rotation_deg | 367.0 | 367.9 | -0.9 |
| robot_peak_pelvis_m | 1.148 | 1.068 | +0.08 |
| pelvis_rise_m | 0.373 | 0.3 | +0.073 |
| robot_airborne_s | 0.58 | 0.56 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 2.9 | 8.2 | -5.3 |
| early_fall | False | False |  |
| plane_dev_max_deg | 9.3 | 9.1 | +0.2 |
| plane_dev_mean_deg | 4.1 | 4.4 | -0.3 |
| leg_asym_deg | 2.0 | 1.6 | +0.4 |
| leg_err_deg | 4.8 | 6.2 | -1.4 |
| feet_dist_max_m | 0.212 | 0.215 | -0.003 |
| feet_dist_touchdown_m | 0.21 | 0.196 | +0.014 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 1 | 0 | +1 |
| flight_hip_err_rad | -0.07 | -0.07 | +0 |
| rot_at_ref_landing_deg | 329.8 | 317.2 | +12.6 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.744 | 0.698 | +0.046 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.165 | 0.197 | -0.032 |
| flight_hip_mean_rad | -1.62 | -1.62 | +0 |
| flight_knee_max_rad | 1.54 | 1.62 | -0.08 |
| flight_knee_overfold_rad | 0.27 | 0.29 | -0.02 |
| knee_sep_min_m | 0.174 | 0.182 | -0.008 |
| track_body_err_m | 0.073 | 0.0825 | -0.0095 |
| track_joint_err | 1.5233 | 1.7302 | -0.207 |
| knee_sep_max_m | 0.269 | 0.284 | -0.015 |
| flight_hip_roll_max_rad | 0.19 | 0.16 | +0.03 |
| flight_hip_yaw_max_rad | 0.28 | 0.23 | +0.05 |
| stand_arm_vel_rms | 0.661 | 0.676 | -0.015 |
| stand_action_change | 0.0392 | 0.0507 | -0.0115 |
| stand_pelvis_speed | 0.047 | 0.14 | -0.093 |
| stand_torso_angvel | 0.201 | 0.466 | -0.265 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 10 of 53 measurements beyond tolerance

- 2.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 39 deg (signed +38), step 45: robot +1.08 vs ref -0.21 rad
- 1.8 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 28 deg (signed +24), step 52: robot +0.50 vs ref -0.69 rad
- 1.8 body:wrist_yaw - left_wrist_yaw_link: mean 0.14 m, max 0.23 m
- 1.4 body:knee - left_knee_link: mean 0.11 m, max 0.17 m
- 1.3 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 119 vs reference 25 rad/s^2
- 1.3 joint:knee - left_knee_joint: mean |err| 19 deg (signed +19), step 26: robot +0.57 vs ref +0.08 rad

**crouch**: 19 of 53 measurements beyond tolerance

- 3.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 53 deg (signed +53), step 82: robot +0.91 vs ref -0.21 rad
- 1.9 body:ankle_roll - left_ankle_roll_link: mean 0.15 m, max 0.29 m
- 1.8 joint:elbow - right_elbow_joint: mean |err| 27 deg (signed -27), step 90: robot +0.03 vs ref +1.13 rad
- 1.8 joint:waist_pitch - waist_pitch_joint: mean |err| 27 deg (signed -15), step 77: robot -0.20 vs ref +0.52 rad
- 1.7 joint:wrist_roll - left_wrist_roll_joint: mean |err| 25 deg (signed +25), step 82: robot +0.42 vs ref -0.11 rad
- 1.7 asymmetry:shoulder_yaw - left/right differ 23 deg vs reference 7 deg

**takeoff**: 24 of 51 measurements beyond tolerance

- 4.9 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 73 deg (signed +73), step 96: robot +0.45 vs ref -1.06 rad
- 4.7 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 70 deg (signed +70), step 97: robot +0.87 vs ref -0.38 rad
- 4.4 asymmetry:wrist_roll - left/right differ 54 deg vs reference 10 deg
- 3.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.31 m, max 0.43 m
- 3.4 joint:elbow - right_elbow_joint: mean |err| 50 deg (signed -50), step 92: robot -0.27 vs ref +0.84 rad
- 3.4 asymmetry:hip_yaw - left/right differ 45 deg vs reference 11 deg

**flight**: 19 of 51 measurements beyond tolerance

- 5.0 asymmetry:wrist_roll - left/right differ 56 deg vs reference 6 deg
- 4.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 72 deg (signed +72), step 107: robot +1.07 vs ref -0.43 rad
- 3.1 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 46 deg (signed +46), step 109: robot +0.08 vs ref -1.20 rad
- 3.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.24 m, max 0.50 m
- 3.0 joint:wrist_roll - left_wrist_roll_joint: mean |err| 44 deg (signed -44), step 106: robot -0.68 vs ref +0.64 rad
- 2.9 body:ankle_roll - left_ankle_roll_link: mean 0.23 m, max 0.44 m

**land**: 17 of 53 measurements beyond tolerance

- 3.0 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 45 deg (signed -45), step 123: robot -1.87 vs ref -0.78 rad
- 2.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.18 m, max 0.23 m
- 2.0 joint:elbow - right_elbow_joint: mean |err| 29 deg (signed +29), step 121: robot +0.55 vs ref -0.44 rad
- 1.9 jitter:elbow - right_elbow_joint: joint acceleration RMS 164 vs reference 24 rad/s^2
- 1.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 27 deg (signed +27), step 121: robot +0.47 vs ref -0.32 rad
- 1.7 body:elbow - right_elbow_link: mean 0.13 m, max 0.17 m

**settle**: 5 of 54 measurements beyond tolerance

- 2.3 jitter:all - mean action change 0.113 (quiet < 0.05)
- 2.1 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 32 deg (signed +32), step 154: robot +0.62 vs ref -0.13 rad
- 1.7 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 29 vs reference 1 rad/s^2
- 1.2 jitter:knee - left_knee_joint: joint acceleration RMS 27 vs reference 2 rad/s^2
- 1.0 jitter:waist_pitch - waist_pitch_joint: joint acceleration RMS 20 vs reference 2 rad/s^2

**stand_after**: 7 of 54 measurements beyond tolerance

- 3.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 53 deg (signed +53), step 187: robot +0.85 vs ref -0.13 rad
- 1.5 asymmetry:shoulder_roll - left/right differ 16 deg vs reference 0 deg
- 1.5 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 22 deg (signed -22), step 171: robot -0.27 vs ref +0.14 rad
- 1.2 body:wrist_yaw - left_wrist_yaw_link: mean 0.10 m, max 0.10 m
- 1.1 joint:shoulder_roll - left_shoulder_roll_joint: mean |err| 17 deg (signed +17), step 160: robot +0.65 vs ref +0.33 rad
- 1.0 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 15 deg (signed +15), step 173: robot +0.96 vs ref +0.67 rad

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.0 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.415 |
| 1.8 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.2 |
| 1.8 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.21 |
| 1.6 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.248 |
| 1.1 | joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.381 |
| 1.7 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.235 |
| 1.9 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.213 |
| 1.5 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.309 |
| 1.0 | body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.446 |
| 1.1 | asymmetry:shoulder_pitch:crouch | dyn_sym | 0.0 | 0.2 | 0.37 |
| 1.2 | asymmetry:shoulder_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.35 |
| 1.7 | asymmetry:shoulder_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.236 |
| 1.3 | asymmetry:elbow:crouch | dyn_sym | 0.0 | 0.2 | 0.311 |
| 2.2 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.149 |
| 3.4 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0535 |
| 1.6 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.251 |
| 1.2 | joint:knee:takeoff | dyn_joint | 0.0 | 0.3 | 0.36 |
| 3.0 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.0944 |
| 3.9 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0454 |
| 2.0 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.199 |
| 1.1 | asymmetry:elbow:takeoff | dyn_sym | 0.0 | 0.2 | 0.372 |
| 4.4 | asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.0224 |
| 1.5 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.271 |
| 1.9 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.183 |
| 1.5 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.261 |
| 1.5 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.265 |
| 1.1 | joint:waist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.369 |
| 3.0 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.0758 |
| 3.1 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.0698 |
| 2.9 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.628 |
| 3.0 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0929 |
| 2.0 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.198 |
| 1.3 | asymmetry:shoulder_pitch:flight | dyn_sym | 0.0 | 0.2 | 0.332 |
| 5.0 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.0125 |
| 1.0 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.438 |
| 2.3 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.158 |
| 2.3 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.5 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.268 |
| 1.7 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.9 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.014 |
| 1.2 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.7 | joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.017 |
| 3.5 | joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0462 |
| 1.5 | joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.281 |
| 3.4 | asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.0535 |
| 4.8 | joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0148 |
| 3.5 | joint:wrist_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.047 |
| 2.6 | joint:wrist_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.106 |
| 1.8 | body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.245 |
| 2.0 | joint:wrist_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.182 |
| 3.0 | joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0733 |
| 2.4 | joint:wrist_roll:takeoff | dyn_joint | 0.0 | 0.3 | 0.12 |
| 2.1 | joint:wrist_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.159 |
| 2.0 | body:elbow:flight | dyn_body | 0.0 | 0.1 | 0.196 |

54 of 170 library checks fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.11| rad (end -0.03), reference max |0.10|
- arm joints mean |err| 8 deg; worst: left_shoulder_roll 12, right_shoulder_yaw 11, left_shoulder_yaw 10, left_shoulder_pitch 9
- action change mean 0.060 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_elbow 11, left_knee 9, left_wrist_roll 8, right_elbow 7
- feet off the floor (> 6 cm): left 0, right 0 of 58 steps
- land (steps 121-129): pelvis speed mean 0.16 m/s, last 0.10; drift 0.02 m
- settle (steps 130-154): pelvis speed mean 0.14 m/s, last 0.04; drift 0.06 m
- stand_after (steps 155-187): pelvis speed mean 0.05 m/s, last 0.06; drift 0.01 m

## F. Training-config audit (what the training actually ran)

- 45 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 5

## F2. Knobs this round trained with vs round 12 (2 differences)

- tracking.scale: 1.5 -> 2.25
- tracking.std_scale: 0.85 -> 0.722

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r12: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7be9b797fba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r13: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x70e9ebb27ba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] fidelity curriculum: r12: tracking weights x1.5, std x0.85
  r13: tracking weights x2.25, std x0.722
- [train_dance] library fixes: r12: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya
  r13: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
