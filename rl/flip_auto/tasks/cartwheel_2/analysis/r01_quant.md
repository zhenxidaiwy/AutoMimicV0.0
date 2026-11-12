# Round 1 - quantitative report (step 1, before any diagnosis)

run `2026-10-25_20-55-55_cw2auto_r01`, best checkpoint `model_1000.pt` (score 1.93), evaluated: model_500.pt 1.27, model_1000.pt 1.93, model_1499.pt 1.649

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | - |  |
| post_s | 5.0 | - |  |
| robot_rotation_deg | 231.0 | - |  |
| robot_max_rotation_deg | 236.0 | - |  |
| robot_peak_pelvis_m | 0.747 | - |  |
| robot_airborne_s | 0.12 | - |  |
| landed_upright | False | - |  |
| end_tilt_deg | 102.7 | - |  |
| pelvis_rise_m | 0.007 | - |  |
| stand_stable | False | - |  |
| stand_feet_d_end | 0.467 | - |  |
| track_body_err_m | 0.6794 | - |  |
| track_joint_err | 4.5906 | - |  |
| post_fell | True | - |  |
| post_tilt_err_max_deg | 87.6 | - |  |
| post_drift_m | 0.695 | - |  |
| post_sway_m | 0.556 | - |  |
| post_pelvis_speed_max | 1.543 | - |  |
| post_action_change | 0.8809 | - |  |
| post_feet_off_steps | 250 | - |  |
| hold_window_s | 2.0 | - |  |
| hold_fell | True | - |  |
| hold_tilt_err_max_deg | 80.3 | - |  |
| hold_height_err_m | 0.641 | - |  |
| hold_pose_err_rad | 0.527 | - |  |
| hold_pelvis_speed_max | 0.494 | - |  |
| hold_drift_m | 0.036 | - |  |
| hold_sway_m | 0.045 | - |  |
| hold_torso_angvel_rms | 2.101 | - |  |
| hold_action_change | 0.3322 | - |  |
| hold_feet_off_steps | 200 | - |  |
| early_fall | False | - |  |
| score | 1.93 | - |  |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-25_20-55-55_cw2auto_r01/eval/_post_auto_model_1000.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.755 | - |  |
| end_pelvis_m | 0.175 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-25_20-55-55_cw2auto_r01/eval/flip_auto_model_1000.mp4 | - |  |

## A2. Robustness (success = rotation >= 330 and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 0.0 | 1.0 | [84.2, 202.1, 282.0] | [76.2, 102.6, 111.9] |
| dr | 0.0 | 0.996 | [73.3, 215.8, 279.0] | [76.7, 104.4, 112.5] |
| delay1 | 0.0 | 1.0 | [69.9, 255.4, 429.4] | [80.3, 117.5, 134.5] |
| delay2 | 0.0 | 1.0 | [101.7, 256.7, 431.6] | [82.1, 127.7, 146.7] |
| kp085 | 0.0 | 1.0 | [92.3, 205.7, 264.2] | [76.7, 102.2, 108.1] |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 30 of 53 measurements beyond tolerance

- 7.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 113 deg (signed +113), step 15: robot +2.56 vs ref -1.81 rad
- 6.0 body:wrist_yaw - left_wrist_yaw_link: mean 0.48 m, max 0.81 m
- 4.7 jitter:shoulder_roll - right_shoulder_roll_joint: joint acceleration RMS 125 vs reference 4 rad/s^2
- 4.7 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 162 vs reference 7 rad/s^2
- 3.9 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 94 vs reference 3 rad/s^2
- 3.6 body:elbow - left_elbow_link: mean 0.29 m, max 0.48 m

**lunge**: 29 of 51 measurements beyond tolerance

- 16.8 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 253 deg (signed +253), step 17: robot +2.70 vs ref -1.81 rad
- 8.6 asymmetry:shoulder_pitch - left/right differ 98 deg vs reference 11 deg
- 7.5 body:wrist_yaw - right_wrist_yaw_link: mean 0.60 m, max 0.67 m
- 5.7 body:ankle_roll - left_ankle_roll_link: mean 0.45 m, max 0.77 m
- 5.2 asymmetry:elbow - left/right differ 55 deg vs reference 3 deg
- 4.7 body:knee - left_knee_link: mean 0.37 m, max 0.54 m

**support**: 32 of 51 measurements beyond tolerance

- 13.4 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 202 deg (signed +202), step 55: robot +2.69 vs ref -2.00 rad
- 13.3 body:ankle_roll - left_ankle_roll_link: mean 1.07 m, max 1.52 m
- 10.0 body:knee - left_knee_link: mean 0.80 m, max 1.05 m
- 7.8 body:hip_roll - left_hip_roll_link: mean 0.62 m, max 0.69 m
- 6.3 body:pelvis - pelvis: mean 0.50 m, max 0.54 m
- 6.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.50 m, max 0.70 m

**land**: 44 of 53 measurements beyond tolerance

- 9.5 body:shoulder_roll - left_shoulder_roll_link: mean 0.76 m, max 0.87 m
- 9.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.75 m, max 0.83 m
- 9.2 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 157 vs reference 1 rad/s^2
- 8.8 body:knee - right_knee_link: mean 0.70 m, max 0.82 m
- 8.2 body:elbow - left_elbow_link: mean 0.65 m, max 0.73 m
- 8.1 body:ankle_roll - right_ankle_roll_link: mean 0.65 m, max 0.86 m

**settle**: 40 of 54 measurements beyond tolerance

- 15.8 body:wrist_yaw - right_wrist_yaw_link: mean 1.26 m, max 1.34 m
- 13.7 body:ankle_roll - right_ankle_roll_link: mean 1.09 m, max 1.19 m
- 12.8 body:elbow - left_elbow_link: mean 1.02 m, max 1.14 m
- 11.6 body:shoulder_roll - left_shoulder_roll_link: mean 0.92 m, max 0.96 m
- 10.3 body:knee - right_knee_link: mean 0.83 m, max 0.86 m
- 9.5 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 143 deg (signed +143), step 106: robot +0.72 vs ref -2.06 rad

**stand_after**: 45 of 54 measurements beyond tolerance

- 41.7 contact:left_foot - left_foot off the floor for 125 of 125 steps
- 41.7 contact:right_foot - right_foot off the floor for 125 of 125 steps
- 18.1 body:wrist_yaw - left_wrist_yaw_link: mean 1.45 m, max 1.49 m
- 15.1 body:elbow - left_elbow_link: mean 1.21 m, max 1.24 m
- 12.5 body:shoulder_roll - right_shoulder_roll_link: mean 1.00 m, max 1.03 m
- 11.7 body:ankle_roll - left_ankle_roll_link: mean 0.93 m, max 1.06 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 3.1 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.0656 |
| 2.6 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.106 |
| 2.9 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.0775 |
| 2.8 | cartwheel_2/asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.0902 |
| 1.8 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.203 |
| 2.3 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.139 |
| 2.1 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.161 |
| 4.0 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.031 |
| 1.2 | cartwheel_2/joint:waist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.351 |
| 2.0 | cartwheel_2/joint:waist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.174 |
| 2.5 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.114 |
| 1.1 | cartwheel_2/joint:wrist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.392 |
| 5.7 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.0106 |
| 7.5 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.00244 |
| 4.7 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.0241 |
| 2.8 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.0859 |
| 5.2 | cartwheel_2/asymmetry:elbow:lunge | dyn_sym | 0.0 | 0.2 | 0.0105 |
| 1.7 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.236 |
| 2.6 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.107 |
| 3.5 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.0464 |
| 1.6 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.244 |
| 1.3 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.31 |
| 13.4 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 8.09e-06 |
| 2.3 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.138 |
| 2.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.166 |
| 2.0 | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | 0.181 |
| 5.0 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.013 |
| 3.9 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0328 |
| 13.3 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 2.37e-05 |
| 6.3 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.00669 |
| 10.0 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.000334 |
| 1.3 | cartwheel_2/asymmetry:ankle_roll:support | dyn_sym | 0.0 | 0.2 | 0.322 |
| 3.2 | cartwheel_2/asymmetry:elbow:support | dyn_sym | 0.0 | 0.2 | 0.0593 |
| 4.2 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0253 |
| 3.1 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.0648 |
| 1.1 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.39 |
| 8.1 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.00151 |
| 9.4 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.000538 |
| 8.8 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.00089 |
| 1.3 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.31 |
| 3.8 | cartwheel_2/asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.0351 |
| 4.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 2.3 | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.133 |
| 2.8 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.0884 |
| 1.9 | cartwheel_2/asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.193 |
| 2.9 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.0789 |
| 6.7 | cartwheel_2/contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 6.7 | cartwheel_2/contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 7.8 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 3.5 | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0453 |
| 3.9 | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0325 |
| 4.4 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0215 |
| 3.0 | cartwheel_2/asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.0748 |
| 3.5 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0467 |
| 41.7 | cartwheel_2/contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 41.7 | cartwheel_2/contact:right_foot:stand_after | dyn_contact | 0.0 | None | - |
| 6.7 | cartwheel_2/jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 18.1 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 5.3e-07 |
| 16.8 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 4.17e-07 |
| 15.8 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 3.31e-06 |
| 15.1 | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | 5.6e-06 |
| 13.7 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 1.8e-05 |
| 12.8 | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | 3.63e-05 |

63 of 80 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 103

- 12.5 body:shoulder_roll:stand_after - right_shoulder_roll_link: mean 1.00 m, max 1.03 m
- 11.7 body:ankle_roll:stand_after - left_ankle_roll_link: mean 0.93 m, max 1.06 m
- 11.6 body:shoulder_roll:settle - left_shoulder_roll_link: mean 0.92 m, max 0.96 m
- 11.1 jitter:ankle_pitch:stand_after - right_ankle_pitch_joint: joint acceleration RMS 303 vs reference 4 rad/s^2
- 10.9 joint:shoulder_pitch:stand_after - right_shoulder_pitch_joint: mean |err| 163 deg (signed +163), step 162: robot +0.86 vs ref -2.24 rad
- 10.3 body:knee:settle - right_knee_link: mean 0.83 m, max 0.86 m
- 9.5 body:shoulder_roll:land - left_shoulder_roll_link: mean 0.76 m, max 0.87 m
- 9.5 joint:shoulder_pitch:settle - right_shoulder_pitch_joint: mean |err| 143 deg (signed +143), step 106: robot +0.72 vs ref -2.06 rad
- 9.2 jitter:wrist_roll:land - left_wrist_roll_joint: joint acceleration RMS 157 vs reference 1 rad/s^2
- 8.7 body:knee:stand_after - left_knee_link: mean 0.70 m, max 0.73 m
- 8.6 asymmetry:shoulder_pitch:lunge - left/right differ 98 deg vs reference 11 deg
- 8.6 body:torso:stand_after - torso_link: mean 0.69 m, max 0.71 m
- 8.2 body:elbow:land - left_elbow_link: mean 0.65 m, max 0.73 m
- 8.0 body:pelvis:stand_after - pelvis: mean 0.64 m, max 0.66 m
- 7.9 body:torso:settle - torso_link: mean 0.63 m, max 0.69 m

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.26| rad (end +0.03), reference max |0.51|
- arm joints mean |err| 53 deg; worst: right_shoulder_pitch 161, left_shoulder_pitch 61, right_elbow 57, left_shoulder_roll 50
- action change mean 0.341 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 190, right_knee 151, right_hip_yaw 146, left_ankle_pitch 120
- feet off the floor (> 6 cm): left 145, right 145 of 145 steps
- land (steps 81-94): pelvis speed mean 0.45 m/s, last 0.63; drift 0.10 m
- settle (steps 95-114): pelvis speed mean 0.31 m/s, last 0.45; drift 0.09 m
- stand_after (steps 115-239): pelvis speed mean 0.21 m/s, last 0.17; drift 0.05 m

## F. Training-config audit (what the training actually ran)

- 27 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
- active library fixes: 0, decider terms: 0

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds []), rounds used 1, GPU 1.6 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | True | == False | FAIL |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.494 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.036 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.045 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 2.101 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.332 | <= 0.1 | FAIL |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 80.3 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.527 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.641 | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 200 | <= 0 | FAIL |
| post_no_fall | eval.post_fell | True | == False | FAIL |
| post_no_drift | eval.post_drift_m | 0.695 | <= 0.15 | FAIL |
| post_posture | eval.post_tilt_err_max_deg | 87.6 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 41.67 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 231.0 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | False | == True | FAIL |

worst unwaived library check: cartwheel_2/contact:left_foot:stand_after

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
- [ ] sheet_480-487.jpg
