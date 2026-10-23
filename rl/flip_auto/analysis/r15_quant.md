# Round 15 - quantitative report (step 1, before any diagnosis)

run `2026-10-23_11-39-43_flipauto_r15`, best checkpoint `model_13499.pt` (score 9.489), evaluated: model_12500.pt 9.487, model_13000.pt 9.484, model_13499.pt 9.489

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| score | 9.489 | 9.61 | -0.121 |
| robot_rotation_deg | 367.5 | 364.9 | +2.6 |
| robot_max_rotation_deg | 370.1 | 366.5 | +3.6 |
| robot_peak_pelvis_m | 1.175 | 1.118 | +0.057 |
| pelvis_rise_m | 0.392 | 0.344 | +0.048 |
| robot_airborne_s | 0.58 | 0.56 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 2.2 | 1.9 | +0.3 |
| early_fall | False | False |  |
| plane_dev_max_deg | 11.2 | 6.4 | +4.8 |
| plane_dev_mean_deg | 6.4 | 2.9 | +3.5 |
| leg_asym_deg | 2.7 | 2.1 | +0.6 |
| leg_err_deg | 6.7 | 5.2 | +1.5 |
| feet_dist_max_m | 0.229 | 0.207 | +0.022 |
| feet_dist_touchdown_m | 0.2 | 0.207 | -0.007 |
| takeoff_offset_steps | -5 | -5 | +0 |
| landing_offset_steps | 1 | 0 | +1 |
| flight_hip_err_rad | -0.25 | -0.11 | -0.14 |
| rot_at_ref_landing_deg | 320.8 | 322.3 | -1.5 |
| ref_rot_at_landing_deg | 323.0 | 323.0 | +0 |
| pelvis_min_after_landing_m | 0.733 | 0.729 | +0.004 |
| stand_stable | True | True |  |
| stand_feet_d_end | 0.186 | 0.162 | +0.024 |
| flight_hip_mean_rad | -1.79 | -1.65 | -0.14 |
| flight_knee_max_rad | 1.73 | 1.62 | +0.11 |
| flight_knee_overfold_rad | 0.33 | 0.33 | +0 |
| knee_sep_min_m | 0.195 | 0.181 | +0.014 |
| track_body_err_m | 0.0698 | 0.0638 | +0.006 |
| track_joint_err | 1.69 | 1.5039 | +0.186 |
| knee_sep_max_m | 0.271 | 0.277 | -0.006 |
| flight_hip_roll_max_rad | 0.16 | 0.17 | -0.01 |
| flight_hip_yaw_max_rad | 0.34 | 0.3 | +0.04 |
| stand_arm_vel_rms | 1.086 | 0.803 | +0.283 |
| stand_action_change | 0.1854 | 0.0527 | +0.133 |
| stand_pelvis_speed | 0.27 | 0.076 | +0.194 |
| stand_torso_angvel | 0.686 | 0.399 | +0.287 |

## A2. Robustness (success = rotation >= 330, upright, pelvis > 0.6 m at the end)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [360.0, 365.1, 370.5] | [2.5, 4.6, 7.1] |
| dr | 1.0 | 0.0 | [358.4, 364.6, 370.1] | [2.3, 4.3, 6.6] |
| delay1 | 0.992 | 0.008 | [357.1, 363.5, 370.9] | [2.6, 4.8, 8.0] |
| delay2 | 0.223 | 0.656 | [201.9, 380.0, 529.3] | [11.7, 98.9, 151.9] |
| kp085 | 1.0 | 0.0 | [357.1, 363.3, 369.4] | [2.2, 4.9, 7.7] |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 9 of 53 measurements beyond tolerance

- 2.7 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 41 deg (signed +41), step 40: robot +1.04 vs ref -0.25 rad
- 1.9 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 28 deg (signed +24), step 52: robot +0.58 vs ref -0.69 rad
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.13 m, max 0.21 m
- 1.6 joint:wrist_roll - right_wrist_roll_joint: mean |err| 24 deg (signed -24), step 39: robot -0.70 vs ref +0.21 rad
- 1.5 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 56 vs reference 8 rad/s^2
- 1.3 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 117 vs reference 25 rad/s^2

**crouch**: 15 of 53 measurements beyond tolerance

- 6.4 asymmetry:wrist_roll - left/right differ 73 deg vs reference 9 deg
- 4.4 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 66 deg (signed +66), step 82: robot +1.17 vs ref -0.21 rad
- 2.5 joint:wrist_roll - right_wrist_roll_joint: mean |err| 38 deg (signed -38), step 89: robot -0.85 vs ref +0.28 rad
- 2.1 body:ankle_roll - left_ankle_roll_link: mean 0.17 m, max 0.25 m
- 1.7 joint:elbow - right_elbow_joint: mean |err| 26 deg (signed -26), step 90: robot -0.10 vs ref +1.13 rad
- 1.6 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 25 deg (signed +25), step 90: robot +0.32 vs ref -0.22 rad

**takeoff**: 22 of 51 measurements beyond tolerance

- 5.7 joint:shoulder_yaw - left_shoulder_yaw_joint: mean |err| 86 deg (signed +86), step 95: robot +0.64 vs ref -1.11 rad
- 5.2 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 78 deg (signed +78), step 93: robot +1.05 vs ref -0.35 rad
- 4.5 asymmetry:wrist_roll - left/right differ 56 deg vs reference 10 deg
- 3.8 joint:elbow - right_elbow_joint: mean |err| 57 deg (signed -57), step 91: robot -0.29 vs ref +0.95 rad
- 3.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.30 m, max 0.37 m
- 2.5 body:ankle_roll - left_ankle_roll_link: mean 0.20 m, max 0.26 m

**flight**: 16 of 51 measurements beyond tolerance

- 5.9 asymmetry:wrist_roll - left/right differ 65 deg vs reference 6 deg
- 4.6 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 69 deg (signed +69), step 98: robot +0.93 vs ref -0.37 rad
- 3.3 joint:wrist_roll - left_wrist_roll_joint: mean |err| 49 deg (signed -49), step 104: robot -0.79 vs ref +0.59 rad
- 3.3 joint:wrist_yaw - right_wrist_yaw_joint: mean |err| 49 deg (signed +49), step 109: robot +0.14 vs ref -1.20 rad
- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.26 m, max 0.44 m
- 3.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.24 m, max 0.37 m

**land**: 15 of 53 measurements beyond tolerance

- 2.7 asymmetry:wrist_roll - left/right differ 43 deg vs reference 15 deg
- 2.5 joint:wrist_roll - right_wrist_roll_joint: mean |err| 37 deg (signed -37), step 122: robot -0.20 vs ref +0.68 rad
- 2.3 joint:wrist_pitch - right_wrist_pitch_joint: mean |err| 34 deg (signed +34), step 121: robot +0.63 vs ref -0.32 rad
- 2.2 joint:elbow - right_elbow_joint: mean |err| 34 deg (signed +34), step 121: robot +0.46 vs ref -0.44 rad
- 2.0 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 520 vs reference 81 rad/s^2
- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.19 m

**settle**: 6 of 54 measurements beyond tolerance

- 2.8 joint:wrist_yaw - left_wrist_yaw_joint: mean |err| 42 deg (signed +42), step 149: robot +0.69 vs ref -0.14 rad
- 2.5 jitter:all - mean action change 0.126 (quiet < 0.05)
- 1.8 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 32 vs reference 1 rad/s^2
- 1.8 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 36 vs reference 2 rad/s^2
- 1.2 joint:knee - left_knee_joint: mean |err| 18 deg (signed +18), step 130: robot +0.73 vs ref +0.23 rad
- 1.1 jitter:knee - left_knee_joint: joint acceleration RMS 25 vs reference 2 rad/s^2

**stand_after**: 22 of 54 measurements beyond tolerance

- 5.7 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 86 vs reference 0 rad/s^2
- 5.5 jitter:knee - left_knee_joint: joint acceleration RMS 82 vs reference 0 rad/s^2
- 4.5 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 68 vs reference 0 rad/s^2
- 4.3 jitter:all - mean action change 0.214 (quiet < 0.05)
- 4.2 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 63 vs reference 0 rad/s^2
- 3.9 jitter:waist_roll - waist_roll_joint: joint acceleration RMS 59 vs reference 0 rad/s^2

**crouch..land**: 0 of 1 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.2 | backflip_3/joint:shoulder_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.339 |
| 1.9 | backflip_3/joint:wrist_yaw:stand | dyn_joint | 0.0 | 0.3 | 0.193 |
| 1.7 | backflip_3/joint:elbow:crouch | dyn_joint | 0.0 | 0.3 | 0.22 |
| 1.2 | backflip_3/joint:shoulder_yaw:crouch | dyn_joint | 0.0 | 0.3 | 0.364 |
| 2.5 | backflip_3/joint:wrist_roll:crouch | dyn_joint | 0.0 | 0.3 | 0.109 |
| 2.1 | backflip_3/body:ankle_roll:crouch | dyn_body | 0.0 | 0.1 | 0.188 |
| 1.5 | backflip_3/body:wrist_yaw:crouch | dyn_body | 0.0 | 0.1 | 0.309 |
| 1.1 | backflip_3/body:knee:crouch | dyn_body | 0.0 | 0.1 | 0.429 |
| 1.3 | backflip_3/asymmetry:ankle_pitch:crouch | dyn_sym | 0.0 | 0.2 | 0.32 |
| 6.4 | backflip_3/asymmetry:wrist_roll:crouch | dyn_sym | 0.0 | 0.2 | 0.00361 |
| 1.8 | backflip_3/joint:ankle_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.202 |
| 3.8 | backflip_3/joint:elbow:takeoff | dyn_joint | 0.0 | 0.3 | 0.0357 |
| 1.5 | backflip_3/joint:hip_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.275 |
| 2.5 | backflip_3/body:ankle_roll:takeoff | dyn_body | 0.0 | 0.1 | 0.136 |
| 3.7 | backflip_3/body:wrist_yaw:takeoff | dyn_body | 0.0 | 0.1 | 0.0509 |
| 1.8 | backflip_3/body:knee:takeoff | dyn_body | 0.0 | 0.1 | 0.235 |
| 1.0 | backflip_3/asymmetry:shoulder_pitch:takeoff | dyn_sym | 0.0 | 0.2 | 0.407 |
| 1.5 | backflip_3/asymmetry:shoulder_yaw:takeoff | dyn_sym | 1.0 | 0.8 | 0.724 |
| 4.5 | backflip_3/asymmetry:wrist_roll:takeoff | dyn_sym | 0.0 | 0.2 | 0.0191 |
| 1.2 | backflip_3/joint:elbow:flight | dyn_joint | 0.0 | 0.3 | 0.36 |
| 1.8 | backflip_3/joint:shoulder_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.209 |
| 1.5 | backflip_3/joint:shoulder_roll:flight | dyn_joint | 0.0 | 0.3 | 0.262 |
| 1.8 | backflip_3/joint:shoulder_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.216 |
| 3.3 | backflip_3/joint:wrist_roll:flight | dyn_joint | 0.0 | 0.3 | 0.0569 |
| 3.3 | backflip_3/joint:wrist_yaw:flight | dyn_joint | 0.0 | 0.3 | 0.0574 |
| 3.2 | backflip_3/body:ankle_roll:flight | dyn_body | 1.0 | 0.5 | 0.595 |
| 3.0 | backflip_3/body:wrist_yaw:flight | dyn_body | 0.0 | 0.1 | 0.0899 |
| 2.2 | backflip_3/body:knee:flight | dyn_body | 0.0 | 0.1 | 0.17 |
| 1.4 | backflip_3/asymmetry:shoulder_roll:flight | dyn_sym | 0.0 | 0.2 | 0.304 |
| 5.9 | backflip_3/asymmetry:wrist_roll:flight | dyn_sym | 0.0 | 0.2 | 0.00566 |
| 1.7 | backflip_3/joint:knee:land | dyn_joint | 0.0 | 0.3 | 0.226 |
| 1.7 | backflip_3/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.256 |
| 2.0 | backflip_3/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.202 |
| 2.5 | backflip_3/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.4 | backflip_3/asymmetry:shoulder_pitch:stand_after | dyn_sym | 0.0 | 0.2 | 0.296 |
| 4.3 | backflip_3/jitter:all:stand_after | dyn_quiet | 2.0 | 1.0 | - |
| 1.8 | backflip_3/jitter:ankle_pitch:settle | dyn_quiet | 0.0 | 1.0 | - |
| 5.7 | backflip_3/joint:shoulder_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.00691 |
| 1.2 | backflip_3/joint:wrist_roll:stand_after | dyn_joint | 0.0 | 0.3 | 0.364 |
| 4.2 | backflip_3/jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.5 | backflip_3/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.7 | backflip_3/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.4 | backflip_3/jitter:shoulder_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | backflip_3/jitter:ankle_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | backflip_3/jitter:knee:settle | dyn_quiet | 0.0 | 1.0 | - |
| 4.5 | backflip_3/jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 5.2 | backflip_3/joint:wrist_pitch:takeoff | dyn_joint | 0.0 | 0.3 | 0.0107 |
| 3.3 | backflip_3/joint:wrist_pitch:stand_after | dyn_joint | 0.0 | 0.3 | 0.0543 |
| 2.7 | backflip_3/jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | backflip_3/joint:wrist_yaw:stand_after | dyn_joint | 0.0 | 0.3 | 0.391 |
| 1.5 | backflip_3/asymmetry:hip_yaw:takeoff | dyn_sym | 0.0 | 0.2 | 0.273 |
| 2.5 | backflip_3/jitter:shoulder_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.5 | backflip_3/jitter:hip_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | backflip_3/jitter:elbow:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.6 | backflip_3/joint:wrist_pitch:flight | dyn_joint | 0.0 | 0.3 | 0.0176 |
| 3.9 | backflip_3/jitter:waist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | backflip_3/jitter:waist_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 4.4 | backflip_3/joint:wrist_pitch:crouch | dyn_joint | 0.0 | 0.3 | 0.0211 |
| 2.7 | backflip_3/joint:wrist_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.0926 |
| 1.7 | backflip_3/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.264 |
| 2.4 | backflip_3/joint:wrist_yaw:takeoff | dyn_joint | 0.0 | 0.3 | 0.126 |
| 1.3 | backflip_3/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.332 |
| 2.5 | backflip_3/joint:wrist_roll:takeoff | dyn_joint | 0.0 | 0.3 | 0.115 |
| 1.8 | backflip_3/body:elbow:flight | dyn_body | 0.0 | 0.1 | 0.233 |
| 2.2 | backflip_3/joint:elbow:land | dyn_joint | 0.0 | 0.3 | 0.141 |
| 1.9 | backflip_3/jitter:waist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.8 | backflip_3/joint:wrist_yaw:settle | dyn_joint | 0.0 | 0.3 | 0.0861 |
| 2.8 | backflip_3/jitter:shoulder_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 2.7 | backflip_3/asymmetry:wrist_roll:land | dyn_sym | 0.0 | 0.2 | 0.0918 |
| 2.5 | backflip_3/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.116 |
| 2.3 | backflip_3/joint:wrist_pitch:land | dyn_joint | 0.0 | 0.3 | 0.136 |
| 2.0 | backflip_3/jitter:ankle_pitch:land | dyn_quiet | 0.0 | 1.0 | - |

72 of 171 checks of task backflip_3 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.12| rad (end -0.06), reference max |0.10|
- arm joints mean |err| 6 deg; worst: right_shoulder_pitch 8, left_shoulder_roll 8, right_elbow 7, left_elbow 6
- action change mean 0.175 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_knee 42, right_hip_yaw 37, left_wrist_roll 36, right_knee 34
- feet off the floor (> 6 cm): left 0, right 0 of 58 steps
- land (steps 121-129): pelvis speed mean 0.13 m/s, last 0.03; drift 0.01 m
- settle (steps 130-154): pelvis speed mean 0.25 m/s, last 0.31; drift 0.12 m
- stand_after (steps 155-187): pelvis speed mean 0.27 m/s, last 0.25; drift 0.16 m

## F. Training-config audit (what the training actually ran)

- 45 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 0.0}, 'term_stand_fail': {'max_d': 0.45, 'max_tilt': 25.0}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 13, decider terms: 5

## F2. Knobs this round trained with vs round 14 (1 differences)

- delay_ms: - -> 25.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r14: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x726f2e02bba0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r15: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7aca57b23ce0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## S. Stop criteria (generic + family:aerial + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.126, -0.094]), rounds used 15, GPU 17.4 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| quiet_after_event | eval.stand_action_change | 0.185 | <= 0.1 | FAIL |
| still_after_event | eval.stand_pelvis_speed | 0.27 | <= 0.1 | FAIL |
| feet_down_after_event | after.feet_off_steps | 0 | <= 0 | pass |
| critic_clean | critic.max_unwaived_severity | 6.44 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 1.0 | >= 0.95 | pass |
| robust_latency_20ms | robust.delay1 | 0.992 | >= 0.95 | pass |
| robust_stiffness | robust.kp085 | 1.0 | >= 0.95 | pass |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 367.5 | >= 330 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |
| no_early_fall | eval.early_fall | False | == False | pass |
| airborne_enough | eval.robot_airborne_s | 0.58 | >= 0.322 | pass |
| in_plane | eval.plane_dev_max_deg | 11.2 | <= 10 | FAIL |

worst unwaived library check: backflip_3/asymmetry:wrist_roll:crouch

## G. Frame sheets to review (every step) - all must be reviewed before the decision

- [ ] sheet_000-039.jpg
- [ ] sheet_040-079.jpg
- [ ] sheet_080-119.jpg
- [ ] sheet_120-159.jpg
- [ ] sheet_160-187.jpg
