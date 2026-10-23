# Round 8 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_01-39-50_flipauto_r08`, best checkpoint `model_5500.pt` (score 9.097), evaluated: model_5500.pt 9.097, model_6000.pt 7.316, model_6499.pt 7.27

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.097 | 8.783 | +0.314 |
| robot_rotation_deg | 344.2 | 372.9 | -28.7 |
| robot_max_rotation_deg | 370.8 | 373.4 | -2.6 |
| robot_peak_pelvis_m | 1.341 | 1.194 | +0.147 |
| pelvis_rise_m | 0.574 | 0.437 | +0.137 |
| robot_airborne_s | 0.74 | 0.6 | +0.14 |
| landed_upright | True | True |  |
| end_tilt_deg | 10.2 | 10.7 | -0.5 |
| early_fall | False | True |  |
| plane_dev_max_deg | 18.5 | 11.5 | +7 |
| plane_dev_mean_deg | 7.6 | 6.0 | +1.6 |
| leg_asym_deg | 4.7 | 2.5 | +2.2 |
| leg_err_deg | 19.6 | 26.8 | -7.2 |
| feet_dist_max_m | 0.322 | 0.378 | -0.056 |
| feet_dist_touchdown_m | 0.241 | 0.173 | +0.068 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 22 | 19 | +3 |
| flight_hip_err_rad | 0.52 | 0.98 | -0.46 |
| rot_at_ref_landing_deg | 285.4 | 312.3 | -26.9 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.705 | 0.755 | -0.05 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.313 | 0.334 | -0.021 |
| flight_hip_mean_rad | -1.03 | - |  |
| flight_knee_max_rad | 2.95 | - |  |
| flight_knee_overfold_rad | 2.06 | - |  |
| knee_sep_min_m | 0.202 | - |  |
| track_body_err_m | 0.1444 | - |  |
| track_joint_err | 2.3985 | - |  |
| knee_sep_max_m | 0.369 | - |  |
| flight_hip_roll_max_rad | 0.28 | - |  |
| flight_hip_yaw_max_rad | 0.44 | - |  |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 16 of 53 measurements beyond tolerance

- 3.6 asymmetry:wrist_roll - left/right differ 39 deg vs reference 2 deg
- 2.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 39 deg (signed +39), step 47: robot +0.85 vs ref -0.19 rad
- 2.2 joint:wrist_roll - right_wrist_roll_joint: mean |err| 34 deg (signed -34), step 37: robot -1.08 vs ref +0.20 rad
- 1.8 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 27 deg (signed +19), step 51: robot +0.31 vs ref -0.69 rad
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.29 m
- 1.6 asymmetry:elbow - left/right differ 21 deg vs reference 5 deg

**crouch**: 18 of 53 measurements beyond tolerance

- 2.1 body:wrist_yaw - left_wrist_yaw_link: mean 0.16 m, max 0.30 m
- 2.0 joint:waist_pitch - waist_pitch_joint: mean |err| 30 deg (signed -18), step 79: robot -0.24 vs ref +0.52 rad
- 2.0 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 30 deg (signed +27), step 89: robot -0.80 vs ref -1.74 rad
- 1.8 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 27 deg (signed +27), step 71: robot +0.46 vs ref -0.13 rad
- 1.5 asymmetry:shoulder_pitch - left/right differ 22 deg vs reference 7 deg
- 1.5 joint:wrist_roll - left_wrist_roll_joint: mean |err| 22 deg (signed +22), step 90: robot +0.70 vs ref -0.42 rad

**takeoff**: 21 of 51 measurements beyond tolerance

- 5.7 asymmetry:shoulder_yaw - left/right differ 59 deg vs reference 2 deg
- 5.0 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 75 deg (signed +75), step 95: robot +0.39 vs ref -1.11 rad
- 3.5 joint:wrist_roll - left_wrist_roll_joint: mean |err| 52 deg (signed +52), step 91: robot +0.77 vs ref -0.42 rad
- 3.2 body:ankle_roll - right_ankle_roll_link: mean 0.25 m, max 0.28 m
- 2.9 joint:elbow - left_elbow_joint: mean |err| 43 deg (signed -43), step 92: robot -0.35 vs ref +0.75 rad
- 2.7 body:wrist_yaw - left_wrist_yaw_link: mean 0.21 m, max 0.27 m

**flight**: 25 of 51 measurements beyond tolerance

- 13.4 asymmetry:shoulder_yaw - left/right differ 138 deg vs reference 4 deg
- 9.4 body:ankle_roll - left_ankle_roll_link: mean 0.75 m, max 1.15 m
- 7.6 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 114 deg (signed +114), step 119: robot +1.92 vs ref -0.53 rad
- 6.9 body:knee - left_knee_link: mean 0.55 m, max 0.76 m
- 5.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.47 m, max 0.65 m
- 5.4 joint:elbow - right_elbow_joint: mean |err| 80 deg (signed +80), step 117: robot +1.33 vs ref -0.33 rad

**land**: 34 of 53 measurements beyond tolerance

- 10.1 body:ankle_roll - left_ankle_roll_link: mean 0.81 m, max 1.19 m
- 7.8 asymmetry:shoulder_yaw - left/right differ 83 deg vs reference 6 deg
- 7.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 114 deg (signed +114), step 124: robot +1.48 vs ref -0.80 rad
- 6.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.51 m, max 0.55 m
- 6.2 asymmetry:shoulder_pitch - left/right differ 65 deg vs reference 3 deg
- 6.1 body:knee - right_knee_link: mean 0.49 m, max 0.66 m

**settle**: 38 of 54 measurements beyond tolerance

- 14.6 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 252 vs reference 1 rad/s^2
- 10.6 jitter:all - mean action change 0.530 (quiet < 0.05)
- 8.9 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 187 vs reference 2 rad/s^2
- 8.4 jitter:hip_roll - right_hip_roll_joint: joint acceleration RMS 138 vs reference 0 rad/s^2
- 7.8 jitter:knee - left_knee_joint: joint acceleration RMS 172 vs reference 2 rad/s^2
- 7.3 jitter:shoulder_roll - left_shoulder_roll_joint: joint acceleration RMS 111 vs reference 0 rad/s^2

**stand_after**: 40 of 54 measurements beyond tolerance

- 10.2 asymmetry:shoulder_yaw - left/right differ 107 deg vs reference 5 deg
- 6.4 asymmetry:shoulder_pitch - left/right differ 67 deg vs reference 4 deg
- 5.9 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 88 vs reference 0 rad/s^2
- 5.7 asymmetry:elbow - left/right differ 64 deg vs reference 7 deg
- 5.3 joint:waist_yaw - waist_yaw_joint: mean |err| 80 deg (signed +80), step 187: robot +1.86 vs ref -0.02 rad
- 4.8 body:wrist_yaw - right_wrist_yaw_link: mean 0.39 m, max 0.43 m

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.6 | joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.254 |
| 1.5 | joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.276 |
| 1.6 | joint:shoulder_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.256 |
| 1.8 | joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.212 |
| 1.6 | asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.244 |
| 3.6 | asymmetry:wrist_roll:stand | dyn_sym | 1.0 | 0.2 | 0.0414 |
| 1.0 | joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.405 |
| 1.3 | joint:hip_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.326 |
| 2.0 | joint:shoulder_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.176 |
| 1.5 | joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.28 |
| 1.5 | body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.313 |
| 2.1 | body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.194 |
| 1.5 | asymmetry:shoulder_pitch:crouch | dyn_sym | 0.0 | 0.2 | 0.274 |
| 1.1 | asymmetry:wrist_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.379 |
| 2.0 | joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.179 |
| 2.9 | joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0812 |
| 1.1 | joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.373 |
| 3.2 | body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.0801 |
| 2.7 | body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.118 |
| 2.4 | body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.151 |
| 1.4 | asymmetry:shoulder_pitch:takeoff | dyn_sym | 0.0 | 0.2 | 0.286 |
| 5.7 | asymmetry:shoulder_yaw:takeoff | dyn_sym | 1.0 | 0.2 | 0.00706 |
| 1.5 | asymmetry:elbow:takeoff | dyn_sym | 0.0 | 0.2 | 0.263 |
| 5.4 | joint:elbow:flight | dyn_joint | 1.0 | 0.3 | 0.00937 |
| 2.1 | joint:hip_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.155 |
| 4.6 | joint:knee:flight | dyn_joint | 1.0 | 0.3 | 0.0178 |
| 4.8 | joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0154 |
| 1.8 | joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.208 |
| 7.6 | joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.00132 |
| 2.2 | joint:waist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.151 |
| 2.5 | joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.116 |
| 1.5 | joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.261 |
| 9.4 | body:ankle_roll:flight | dyn_body | 1.0 | 0.1 | 0.000557 |
| 5.9 | body:wrist_yaw:flight | dyn_body | 1.0 | 0.1 | 0.00901 |
| 6.9 | body:knee:flight | dyn_body | 0.0 | 0.1 | 0.00409 |
| 2.7 | asymmetry:shoulder_pitch:flight | dyn_sym | 0.0 | 0.2 | 0.0971 |
| 1.5 | asymmetry:shoulder_roll:flight | dyn_sym | 0.0 | 0.2 | 0.281 |
| 13.4 | asymmetry:shoulder_yaw:flight | dyn_sym | 1.0 | 0.2 | 8.6e-06 |
| 4.6 | asymmetry:elbow:flight | dyn_sym | 0.0 | 0.2 | 0.018 |
| 1.5 | asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.272 |
| 1.4 | joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.301 |
| 1.1 | joint:knee:land | dyn_joint | 0.0 | 0.3 | 0.388 |
| 10.1 | body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.000313 |
| 6.3 | body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.00636 |
| 6.1 | body:knee:land | dyn_body | 0.0 | 0.1 | 0.00771 |
| 6.2 | asymmetry:shoulder_pitch:land | dyn_sym | 0.0 | 0.2 | 0.0044 |
| 4.0 | asymmetry:shoulder_roll:land | dyn_sym | 0.0 | 0.2 | 0.0314 |
| 7.8 | asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.00114 |
| 1.8 | asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.208 |
| 3.0 | contact:left_foot:land | dyn_contact | 0.0 | None | - |
| 3.0 | contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 2.1 | joint:elbow:settle | dyn_joint | 0.0 | 0.3 | 0.16 |
| 1.2 | joint:shoulder_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.357 |
| 1.5 | joint:wrist_roll:settle | dyn_joint | 0.0 | 0.3 | 0.278 |
| 2.3 | asymmetry:shoulder_pitch:settle | dyn_sym | 0.0 | 0.2 | 0.136 |
| 1.2 | asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | 0.365 |
| 1.5 | asymmetry:shoulder_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.282 |
| 3.2 | asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.0625 |
| 1.7 | asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.234 |
| 2.3 | contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 2.0 | contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 10.6 | jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.7 | asymmetry:hip_roll:stand_after | dyn_sym | 1.0 | 0.2 | 0.229 |
| 6.4 | asymmetry:shoulder_pitch:stand_after | dyn_sym | 1.0 | 0.2 | 0.00392 |
| 1.8 | asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.206 |
| 10.2 | asymmetry:shoulder_yaw:stand_after | dyn_sym | 1.0 | 0.2 | 0.000133 |
| 5.7 | asymmetry:elbow:stand_after | dyn_sym | 1.0 | 0.2 | 0.0069 |
| 3.6 | asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.045 |
| 3.7 | contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 1.3 | contact:right_foot:stand_after | dyn_contact | 0.0 | None | - |
| 2.6 | jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 14.6 | jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 5.3 | joint:waist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.00954 |
| 5.0 | joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.0128 |
| 8.9 | jitter:hip_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 2.7 | joint:elbow:stand_after | dyn_joint | 0.0 | 0.3 | 0.0919 |
| 4.0 | joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.0308 |

77 of 144 library checks fail.

## D. Deviations no check covers yet (severity > 2): 50

- 8.4 jitter:hip_roll:settle - right_hip_roll_joint: joint acceleration RMS 138 vs reference 0 rad/s^2
- 7.8 jitter:knee:settle - left_knee_joint: joint acceleration RMS 172 vs reference 2 rad/s^2
- 7.6 joint:shoulder_pitch:land - left_shoulder_pitch_joint: mean |err| 114 deg (signed +114), step 124: robot +1.48 vs ref -0.80 rad
- 7.3 jitter:shoulder_roll:settle - left_shoulder_roll_joint: joint acceleration RMS 111 vs reference 0 rad/s^2
- 6.5 jitter:shoulder_yaw:settle - right_shoulder_yaw_joint: joint acceleration RMS 140 vs reference 2 rad/s^2
- 6.0 jitter:waist_roll:settle - waist_roll_joint: joint acceleration RMS 92 vs reference 0 rad/s^2
- 5.9 jitter:ankle_pitch:stand_after - right_ankle_pitch_joint: joint acceleration RMS 88 vs reference 0 rad/s^2
- 5.7 jitter:hip_pitch:settle - left_hip_pitch_joint: joint acceleration RMS 127 vs reference 2 rad/s^2
- 5.3 jitter:waist_pitch:settle - waist_pitch_joint: joint acceleration RMS 103 vs reference 2 rad/s^2
- 5.2 jitter:waist_roll:land - waist_roll_joint: joint acceleration RMS 132 vs reference 4 rad/s^2
- 5.0 body:elbow:land - left_elbow_link: mean 0.40 m, max 0.48 m
- 5.0 jitter:shoulder_pitch:settle - right_shoulder_pitch_joint: joint acceleration RMS 167 vs reference 6 rad/s^2
- 5.0 joint:shoulder_yaw:land - left_shoulder_yaw_joint: mean |err| 75 deg (signed +75), step 121: robot +1.77 vs ref -0.48 rad
- 5.0 jitter:wrist_pitch:settle - left_wrist_pitch_joint: joint acceleration RMS 108 vs reference 2 rad/s^2
- 4.9 jitter:waist_yaw:settle - waist_yaw_joint: joint acceleration RMS 97 vs reference 2 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |1.86| rad (end +1.86), reference max |0.10|
- arm joints mean |err| 29 deg; worst: right_shoulder_yaw 39, right_elbow 35, left_elbow 30, right_shoulder_pitch 29
- action change mean 0.300 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 102, right_ankle_pitch 99, right_hip_yaw 85, left_wrist_roll 78
- feet off the floor (> 6 cm): left 18, right 10 of 58 steps

## F. Training-config audit (what the training actually ran)

- 26 reward terms in the log; flip_* terms of the current code missing from training: ['flip_stand_quiet']
- root orientation term: motion_global_root_ori (global, NOT replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 30.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 0, decider terms: 0

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
