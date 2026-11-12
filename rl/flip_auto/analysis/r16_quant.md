# Round 16 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_18-23-14_flipauto_r16`, best checkpoint `model_14998.pt` (score 9.576), evaluated: model_14000.pt 9.535, model_14500.pt 9.471, model_14998.pt 9.576

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.576 | 9.489 | +0.087 |
| robot_rotation_deg | 363.1 | 367.5 | -4.4 |
| robot_max_rotation_deg | 366.5 | 370.1 | -3.6 |
| robot_peak_pelvis_m | 1.214 | 1.175 | +0.039 |
| pelvis_rise_m | 0.438 | 0.392 | +0.046 |
| robot_airborne_s | 0.6 | 0.58 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 3.5 | 2.2 | +1.3 |
| early_fall | False | False |  |
| plane_dev_max_deg | 5.8 | 11.2 | -5.4 |
| plane_dev_mean_deg | 3.5 | 6.4 | -2.9 |
| leg_asym_deg | 2.0 | 2.7 | -0.7 |
| leg_err_deg | 6.6 | 6.7 | -0.1 |
| feet_dist_max_m | 0.214 | 0.229 | -0.015 |
| feet_dist_touchdown_m | 0.18 | 0.2 | -0.02 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 2 | 1 | +1 |
| flight_hip_err_rad | -0.23 | -0.25 | +0.02 |
| rot_at_ref_landing_deg | 318.9 | 320.8 | -1.9 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.743 | 0.733 | +0.01 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.148 | 0.186 | -0.038 |
| flight_hip_mean_rad | -1.78 | -1.79 | +0.01 |
| flight_knee_max_rad | 1.71 | 1.73 | -0.02 |
| flight_knee_overfold_rad | 0.3 | 0.33 | -0.03 |
| knee_sep_min_m | 0.185 | 0.195 | -0.01 |
| track_body_err_m | 0.0699 | 0.0698 | +0.0001 |
| track_joint_err | 1.6171 | 1.69 | -0.0729 |
| knee_sep_max_m | 0.272 | 0.271 | +0.001 |
| flight_hip_roll_max_rad | 0.13 | 0.16 | -0.03 |
| flight_hip_yaw_max_rad | 0.27 | 0.34 | -0.07 |
| stand_arm_vel_rms | 0.47 | 1.086 | -0.616 |
| stand_action_change | 0.0723 | 0.1854 | -0.113 |
| stand_pelvis_speed | 0.117 | 0.27 | -0.153 |
| stand_torso_angvel | 0.412 | 0.686 | -0.274 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-23_18-23-14_flipauto_r16/eval/_post_auto_model_14998.npz | - |  |
| clip_s | 8.8 | - |  |
| post_s | 5.0 | - |  |
| ref_rotation_deg | 365.0 | - |  |
| ref_peak_pelvis_m | 1.108 | - |  |
| end_pelvis_m | 0.779 | - |  |
| post_fell | False | - |  |
| post_tilt_err_max_deg | 3.4 | - |  |
| post_drift_m | 0.114 | - |  |
| post_sway_m | 0.069 | - |  |
| post_pelvis_speed_max | 0.208 | - |  |
| post_action_change | 0.0671 | - |  |
| post_feet_off_steps | 0 | - |  |
| legs_crossed_frac | 0.0 | - |  |
| hold_window_s | 0.66 | - |  |
| hold_fell | False | - |  |
| hold_tilt_err_max_deg | 2.3 | - |  |
| hold_height_err_m | 0.015 | - |  |
| hold_pose_err_rad | 0.155 | - |  |
| hold_pelvis_speed_max | 0.263 | - |  |
| hold_drift_m | 0.048 | - |  |
| hold_sway_m | 0.036 | - |  |
| hold_torso_angvel_rms | 0.561 | - |  |
| hold_action_change | 0.0902 | - |  |
| hold_feet_off_steps | 0 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-23_18-23-14_flipauto_r16/eval/flip_auto_model_14998.mp4 | - |  |

## A2. Robustness (success = rotation >= 330 and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 0.957 | 0.0 | [358.3, 364.1, 370.9] | [2.7, 4.5, 6.7] |
| dr | 0.422 | 0.0 | [357.3, 363.9, 370.7] | [3.2, 4.9, 7.3] |
| delay1 | 0.27 | 0.023 | [355.0, 363.6, 370.6] | [4.5, 6.9, 12.9] |
| delay2 | 0.0 | 0.93 | [276.8, 523.5, 975.2] | [103.1, 146.8, 176.2] |
| kp085 | 0.348 | 0.016 | [357.4, 365.1, 373.8] | [3.9, 6.1, 9.4] |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 8 of 53 measurements beyond tolerance

- 2.4 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 36 deg (signed +16), step 51: robot +0.65 vs ref -0.69 rad
- 2.0 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 30 deg (signed +21), step 59: robot +0.80 vs ref -0.20 rad
- 1.7 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 128 vs reference 20 rad/s^2
- 1.5 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 56 vs reference 8 rad/s^2
- 1.4 joint:knee - left_knee_joint: mean |err| 21 deg (signed +21), step 64: robot +0.89 vs ref +0.24 rad
- 1.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.11 m, max 0.24 m

**crouch**: 15 of 53 measurements beyond tolerance

- 3.9 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 59 deg (signed +59), step 90: robot +1.12 vs ref -0.18 rad
- 3.2 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 48 deg (signed +48), step 74: robot +0.95 vs ref -0.07 rad
- 2.2 joint:elbow - right_elbow_joint: mean |err| 33 deg (signed -33), step 89: robot +0.02 vs ref +1.34 rad
- 1.9 body:ankle_roll - right_ankle_roll_link: mean 0.15 m, max 0.27 m
- 1.9 asymmetry:shoulder_yaw - left/right differ 26 deg vs reference 7 deg
- 1.4 joint:ankle_roll - right_ankle_roll_joint: mean |err| 21 deg (signed +21), step 79: robot +0.26 vs ref -0.24 rad

**takeoff**: 18 of 51 measurements beyond tolerance

- 5.5 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 83 deg (signed +83), step 97: robot +0.77 vs ref -1.04 rad
- 5.3 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 80 deg (signed +80), step 92: robot +1.09 vs ref -0.33 rad
- 3.8 body:wrist_yaw - left_wrist_yaw_link: mean 0.31 m, max 0.40 m
- 3.2 joint:elbow - left_elbow_joint: mean |err| 48 deg (signed -48), step 93: robot -0.36 vs ref +0.66 rad
- 2.9 body:ankle_roll - right_ankle_roll_link: mean 0.23 m, max 0.27 m
- 2.2 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 33 deg (signed +33), step 94: robot +0.44 vs ref -0.60 rad

**flight**: 16 of 51 measurements beyond tolerance

- 5.2 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 77 deg (signed +77), step 107: robot +1.19 vs ref -0.43 rad
- 3.4 body:ankle_roll - left_ankle_roll_link: mean 0.27 m, max 0.40 m
- 3.2 body:wrist_yaw - right_wrist_yaw_link: mean 0.25 m, max 0.40 m
- 2.7 joint:wrist_roll - left_wrist_roll_joint: mean |err| 40 deg (signed -40), step 107: robot -0.78 vs ref +0.70 rad
- 2.3 body:knee - left_knee_link: mean 0.18 m, max 0.25 m
- 2.2 asymmetry:wrist_roll - left/right differ 28 deg vs reference 6 deg

**land**: 13 of 53 measurements beyond tolerance

- 2.5 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 38 deg (signed +38), step 124: robot +0.93 vs ref +0.23 rad
- 2.3 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 585 vs reference 81 rad/s^2
- 1.9 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 28 deg (signed +28), step 121: robot +0.49 vs ref -0.32 rad
- 1.8 joint:elbow - right_elbow_joint: mean |err| 27 deg (signed +27), step 123: robot +0.25 vs ref -0.42 rad
- 1.6 body:wrist_yaw - right_wrist_yaw_link: mean 0.13 m, max 0.16 m
- 1.5 jitter:waist_roll - waist_roll_joint: joint acceleration RMS 38 vs reference 4 rad/s^2

**settle**: 13 of 54 measurements beyond tolerance

- 3.4 jitter:all - mean action change 0.172 (quiet < 0.05)
- 2.8 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 49 vs reference 1 rad/s^2
- 1.8 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 38 vs reference 2 rad/s^2
- 1.7 jitter:ankle_roll - right_ankle_roll_joint: joint acceleration RMS 27 vs reference 0 rad/s^2
- 1.6 jitter:shoulder_roll - left_shoulder_roll_joint: joint acceleration RMS 24 vs reference 0 rad/s^2
- 1.6 joint:wrist_pitch - left_wrist_pitch_joint: mean |err| 24 deg (signed -24), step 154: robot -1.03 vs ref -0.18 rad

**stand_after**: 11 of 54 measurements beyond tolerance

- 3.7 joint:wrist_pitch - left_wrist_pitch_joint: mean |err| 55 deg (signed -55), step 170: robot -1.20 vs ref -0.18 rad
- 3.3 jitter:hip_yaw - left_hip_yaw_joint: joint acceleration RMS 49 vs reference 0 rad/s^2
- 2.5 jitter:knee - left_knee_joint: joint acceleration RMS 38 vs reference 0 rad/s^2
- 2.3 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 35 vs reference 0 rad/s^2
- 2.0 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 29 deg (signed -29), step 169: robot -0.39 vs ref +0.14 rad
- 1.7 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 26 vs reference 0 rad/s^2

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.4 | backflip_3/joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.121 |
| 2.2 | backflip_3/joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.144 |
| 1.0 | backflip_3/joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.413 |
| 1.2 | backflip_3/joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.347 |
| 1.9 | backflip_3/body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.215 |
| 1.3 | backflip_3/body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.34 |
| 1.2 | backflip_3/body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.392 |
| 1.0 | backflip_3/asymmetry:shoulder_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.41 |
| 1.9 | backflip_3/asymmetry:shoulder_yaw:crouch | dyn_sym | 0.0 | 0.2 | 0.191 |
| 1.3 | backflip_3/asymmetry:wrist_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.316 |
| 2.2 | backflip_3/joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.148 |
| 3.2 | backflip_3/joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0597 |
| 1.3 | backflip_3/joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.316 |
| 2.9 | backflip_3/body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.102 |
| 3.8 | backflip_3/body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0461 |
| 2.2 | backflip_3/body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.173 |
| 1.1 | backflip_3/joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.38 |
| 1.5 | backflip_3/joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.261 |
| 1.4 | backflip_3/joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.302 |
| 2.1 | backflip_3/joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.154 |
| 2.7 | backflip_3/joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.098 |
| 1.2 | backflip_3/joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.355 |
| 3.4 | backflip_3/body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.582 |
| 3.2 | backflip_3/body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0789 |
| 2.3 | backflip_3/body:knee:flight | dyn_body | 0.0 | 0.1 | 0.164 |
| 2.2 | backflip_3/asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.151 |
| 1.3 | backflip_3/joint:knee:land | dyn_joint | 0.0 | 0.3 | 0.311 |
| 1.4 | backflip_3/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.315 |
| 1.6 | backflip_3/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.279 |
| 3.4 | backflip_3/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.2 | backflip_3/asymmetry:shoulder_yaw:stand_after | dyn_sym | 1.0 | 0.8 | 0.771 |
| 1.7 | backflip_3/jitter:all:stand_after | dyn_quiet | 2.0 | 1.0 | - |
| 2.8 | backflip_3/jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 5.5 | backflip_3/joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.00819 |
| 1.8 | backflip_3/jitter:hip_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 2.3 | backflip_3/jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.5 | backflip_3/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 3.3 | backflip_3/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | backflip_3/jitter:shoulder_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.7 | backflip_3/jitter:ankle_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.4 | backflip_3/jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | backflip_3/jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.3 | backflip_3/joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.00944 |
| 3.7 | backflip_3/joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0404 |
| 1.7 | backflip_3/jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | backflip_3/joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.181 |
| 1.9 | backflip_3/asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.187 |
| 5.2 | backflip_3/joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0111 |
| 3.9 | backflip_3/joint:wrist_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.0322 |
| 2.0 | backflip_3/joint:wrist_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.172 |
| 1.4 | backflip_3/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.331 |
| 2.2 | backflip_3/joint:wrist_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.149 |
| 1.2 | backflip_3/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.338 |
| 1.6 | backflip_3/joint:wrist_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.251 |
| 1.8 | backflip_3/body:elbow:flight | dyn_body | 0.0 | 0.1 | 0.238 |
| 1.8 | backflip_3/joint:elbow:land | dyn_joint | 0.0 | 0.3 | 0.208 |
| 1.5 | backflip_3/jitter:waist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | backflip_3/joint:wrist_yaw:settle | dyn_joint | 0.0 | 0.3 | 0.347 |
| 1.9 | backflip_3/joint:wrist_pitch:land | dyn_joint | 0.0 | 0.3 | 0.195 |
| 2.3 | backflip_3/jitter:ankle_pitch:land | dyn_quiet | 0.0 | 1.0 | - |
| 3.2 | backflip_3/joint:wrist_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.0629 |
| 2.5 | backflip_3/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.108 |

62 of 174 checks of task backflip_3 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.14| rad (end -0.00), reference max |0.10|
- arm joints mean |err| 5 deg; worst: left_shoulder_yaw 8, right_shoulder_roll 6, right_elbow 6, left_shoulder_roll 5
- action change mean 0.119 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_ankle_pitch 28, left_hip_yaw 26, right_ankle_pitch 26, left_knee 23
- feet off the floor (> 6 cm): left 0, right 0 of 60 steps
- land (steps 121-129): pelvis speed mean 0.35 m/s, last 0.18; drift 0.05 m
- settle (steps 130-154): pelvis speed mean 0.24 m/s, last 0.18; drift 0.11 m
- stand_after (steps 155-189): pelvis speed mean 0.13 m/s, last 0.13; drift 0.04 m

## F. Training-config audit (what the training actually ran)

- 45 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 5

## F2. Knobs this round trained with vs round 15 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r15: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7aca57b23ce0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r16: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x731e0ed7bce0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r15: [('lib_asymmetry_wrist_roll_stand', 1.0), ('lib_contact_left_foot_stand', 2.0), ('lib_contact_right_foot_stand', 2.0), ('lib_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_joint_knee_flight', 1.0), ('lib_body_ankle_roll_flight', 1.0), ('lib_asymmetry_shoulder_ya
  r16: [('lib_backflip_3_asymmetry_wrist_roll_stand', 1.0), ('lib_backflip_3_contact_left_foot_stand', 2.0), ('lib_backflip_3_contact_right_foot_stand', 2.0), ('lib_backflip_3_asymmetry_shoulder_yaw_takeoff', 1.0), ('lib_backflip_3_joint_knee_flight', 1.0), ('lib_bac

## S. Stop criteria (generic + family:aerial + task; stop_criteria.json)

**not done** - converged: True (rel. improvement of the last rounds [-0.094, -0.0014]), rounds used 16, GPU 19.1 h, over budget: False, waivers in force: 1

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 0.66 | >= 2.0 | FAIL |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.263 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.048 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.036 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.561 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.09 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 2.3 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.155 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.015 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.114 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 3.4 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 5.51 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.422 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.27 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.348 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 363.1 | >= 330 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |
| no_early_fall | eval.early_fall | False | == False | pass |
| airborne_enough | eval.robot_airborne_s | 0.6 | >= 0.322 | pass |
| in_plane | eval.plane_dev_max_deg | 5.8 | <= 10 | pass |

worst unwaived library check: backflip_3/joint:shoulder_yaw:takeoff

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
- [ ] sheet_400-437.jpg
