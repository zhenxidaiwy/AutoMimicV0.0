# Round 12 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_07-20-15_flipauto_r12`, best checkpoint `model_10000.pt` (score 9.519), evaluated: model_10000.pt 9.519, model_10500.pt 9.498, model_10998.pt 9.495

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.519 | 9.433 | +0.086 |
| robot_rotation_deg | 367.9 | 371.2 | -3.3 |
| robot_max_rotation_deg | 367.9 | 371.4 | -3.5 |
| robot_peak_pelvis_m | 1.068 | 1.176 | -0.108 |
| pelvis_rise_m | 0.3 | 0.421 | -0.121 |
| robot_airborne_s | 0.56 | 0.58 | -0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 8.2 | 6.4 | +1.8 |
| early_fall | False | False |  |
| plane_dev_max_deg | 9.1 | 5.3 | +3.8 |
| plane_dev_mean_deg | 4.4 | 3.2 | +1.2 |
| leg_asym_deg | 1.6 | 2.2 | -0.6 |
| leg_err_deg | 6.2 | 4.9 | +1.3 |
| feet_dist_max_m | 0.215 | 0.218 | -0.003 |
| feet_dist_touchdown_m | 0.196 | 0.198 | -0.002 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 0 | 1 | -1 |
| flight_hip_err_rad | -0.07 | -0.04 | -0.03 |
| rot_at_ref_landing_deg | 317.2 | 324.1 | -6.9 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.698 | 0.746 | -0.048 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.197 | 0.301 | -0.104 |
| flight_hip_mean_rad | -1.62 | -1.58 | -0.04 |
| flight_knee_max_rad | 1.62 | 1.56 | +0.06 |
| flight_knee_overfold_rad | 0.29 | 0.26 | +0.03 |
| knee_sep_min_m | 0.182 | 0.18 | +0.002 |
| track_body_err_m | 0.0825 | 0.1056 | -0.0231 |
| track_joint_err | 1.7302 | 2.0797 | -0.349 |
| knee_sep_max_m | 0.284 | 0.287 | -0.003 |
| flight_hip_roll_max_rad | 0.16 | 0.19 | -0.03 |
| flight_hip_yaw_max_rad | 0.23 | 0.23 | +0 |
| stand_arm_vel_rms | 0.676 | 2.219 | -1.54 |
| stand_action_change | 0.0507 | 0.368 | -0.317 |
| stand_pelvis_speed | 0.14 | 1.035 | -0.895 |
| stand_torso_angvel | 0.466 | 1.353 | -0.887 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 13 of 53 measurements beyond tolerance

- 3.2 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 48 deg (signed +48), step 53: robot +1.21 vs ref -0.15 rad
- 2.7 contact:left_foot - left_foot off the floor for 8 of 71 steps
- 2.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.19 m, max 0.34 m
- 2.1 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 32 deg (signed +29), step 51: robot -1.62 vs ref -2.75 rad
- 2.1 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 32 deg (signed +23), step 52: robot +0.45 vs ref -0.69 rad
- 1.9 joint:wrist_roll - left_wrist_roll_joint: mean |err| 29 deg (signed +18), step 38: robot +0.78 vs ref -0.21 rad

**crouch**: 18 of 53 measurements beyond tolerance

- 3.7 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 55 deg (signed +55), step 90: robot +0.97 vs ref -0.18 rad
- 2.6 joint:elbow - right_elbow_joint: mean |err| 40 deg (signed -40), step 89: robot +0.07 vs ref +1.34 rad
- 2.6 asymmetry:elbow - left/right differ 29 deg vs reference 3 deg
- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.21 m
- 2.0 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 30 deg (signed +30), step 83: robot +0.54 vs ref -0.06 rad
- 2.0 asymmetry:shoulder_roll - left/right differ 24 deg vs reference 4 deg

**takeoff**: 21 of 51 measurements beyond tolerance

- 5.0 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 75 deg (signed +75), step 97: robot +0.99 vs ref -0.38 rad
- 4.7 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 71 deg (signed +71), step 94: robot +0.21 vs ref -1.15 rad
- 3.9 body:wrist_yaw - left_wrist_yaw_link: mean 0.31 m, max 0.42 m
- 3.3 joint:elbow - right_elbow_joint: mean |err| 50 deg (signed -50), step 91: robot -0.21 vs ref +0.95 rad
- 3.0 body:ankle_roll - left_ankle_roll_link: mean 0.24 m, max 0.29 m
- 2.8 asymmetry:hip_yaw - left/right differ 39 deg vs reference 11 deg

**flight**: 16 of 51 measurements beyond tolerance

- 4.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 67 deg (signed +67), step 107: robot +1.01 vs ref -0.43 rad
- 3.7 asymmetry:wrist_roll - left/right differ 43 deg vs reference 6 deg
- 3.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.26 m, max 0.51 m
- 3.3 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 49 deg (signed +49), step 109: robot +0.17 vs ref -1.20 rad
- 2.9 body:ankle_roll - left_ankle_roll_link: mean 0.23 m, max 0.43 m
- 2.1 body:knee - left_knee_link: mean 0.17 m, max 0.33 m

**land**: 15 of 53 measurements beyond tolerance

- 1.8 joint:knee - left_knee_joint: mean |err| 28 deg (signed +28), step 126: robot +0.95 vs ref +0.28 rad
- 1.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 27 deg (signed +27), step 121: robot +0.27 vs ref -0.32 rad
- 1.7 joint:elbow - right_elbow_joint: mean |err| 26 deg (signed +26), step 121: robot +0.27 vs ref -0.44 rad
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.19 m
- 1.7 body:ankle_roll - left_ankle_roll_link: mean 0.14 m, max 0.17 m
- 1.7 jitter:shoulder_pitch - right_shoulder_pitch_joint: joint acceleration RMS 136 vs reference 21 rad/s^2

**settle**: 8 of 54 measurements beyond tolerance

- 2.9 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 50 vs reference 1 rad/s^2
- 1.7 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 26 deg (signed -26), step 150: robot -0.79 vs ref -0.15 rad
- 1.7 jitter:all - mean action change 0.086 (quiet < 0.05)
- 1.7 jitter:knee - right_knee_joint: joint acceleration RMS 41 vs reference 3 rad/s^2
- 1.5 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 23 deg (signed +23), step 154: robot +0.36 vs ref -0.13 rad
- 1.4 joint:knee - left_knee_joint: mean |err| 20 deg (signed +20), step 149: robot +0.49 vs ref +0.08 rad

**stand_after**: 6 of 54 measurements beyond tolerance

- 2.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 42 deg (signed +42), step 187: robot +0.90 vs ref -0.13 rad
- 1.9 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 28 deg (signed -28), step 155: robot -0.78 vs ref -0.17 rad
- 1.9 joint:wrist_roll - left_wrist_roll_joint: mean |err| 28 deg (signed -28), step 187: robot -0.51 vs ref +0.10 rad
- 1.4 asymmetry:shoulder_roll - left/right differ 15 deg vs reference 0 deg
- 1.0 body:wrist_yaw - left_wrist_yaw_link: mean 0.08 m, max 0.11 m
- 1.0 joint:knee - left_knee_joint: mean |err| 15 deg (signed +15), step 155: robot +0.42 vs ref +0.06 rad

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.1 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.156 |
| 1.1 | joint:shoulder_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.389 |
| 2.1 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.16 |
| 2.7 | contact:left_foot:stand | dyn_contact | 2.0 | None | - |
| 2.6 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.0994 |
| 1.2 | joint:hip_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.365 |
| 1.2 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.355 |
| 1.2 | joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.352 |
| 1.6 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.242 |
| 1.8 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.232 |
| 2.0 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.201 |
| 1.2 | body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.398 |
| 1.1 | asymmetry:hip_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.397 |
| 2.0 | asymmetry:shoulder_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.182 |
| 2.6 | asymmetry:elbow:crouch | dyn_sym | 0.0 | 0.2 | 0.103 |
| 2.3 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.135 |
| 3.3 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0544 |
| 1.7 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.222 |
| 1.2 | joint:knee:takeoff | dyn_joint | 0.0 | 0.3 | 0.364 |
| 3.0 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.0904 |
| 3.9 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0437 |
| 2.0 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.201 |
| 1.1 | asymmetry:hip_pitch:takeoff | dyn_sym | 0.0 | 0.2 | 0.396 |
| 1.4 | joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.307 |
| 1.6 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.238 |
| 1.4 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.286 |
| 1.7 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.222 |
| 1.8 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.199 |
| 3.3 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.0586 |
| 2.9 | body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.628 |
| 3.3 | body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0715 |
| 2.1 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.191 |
| 3.7 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.0383 |
| 1.8 | joint:knee:land | dyn_joint | 0.0 | 0.3 | 0.2 |
| 1.7 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.251 |
| 1.7 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.248 |
| 1.1 | asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.371 |
| 1.1 | joint:wrist_roll:settle | dyn_joint | 0.0 | 0.3 | 0.379 |
| 1.7 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.4 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.29 |
| 2.9 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.7 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0164 |
| 1.9 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.195 |
| 1.7 | jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 5.0 | joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.0124 |
| 2.8 | joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0877 |
| 1.9 | joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.193 |
| 2.8 | asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.0878 |
| 4.5 | joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.02 |
| 3.7 | joint:wrist_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.0406 |
| 3.2 | joint:wrist_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.0598 |
| 2.3 | body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.155 |
| 2.1 | joint:wrist_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.155 |

53 of 166 library checks fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.07| rad (end -0.03), reference max |0.10|
- arm joints mean |err| 6 deg; worst: left_shoulder_roll 8, left_shoulder_yaw 8, left_elbow 6, right_shoulder_yaw 6
- action change mean 0.061 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_elbow 10, right_elbow 8, right_shoulder_pitch 7, left_knee 7
- feet off the floor (> 6 cm): left 0, right 0 of 58 steps
- land (steps 121-129): pelvis speed mean 0.37 m/s, last 0.23; drift 0.05 m
- settle (steps 130-154): pelvis speed mean 0.09 m/s, last 0.11; drift 0.02 m
- stand_after (steps 155-187): pelvis speed mean 0.15 m/s, last 0.11; drift 0.09 m

## F. Training-config audit (what the training actually ran)

- 44 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 4

## F2. Knobs this round trained with vs round 11 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r11: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x78131a71fba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r12: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7be9b797fba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
