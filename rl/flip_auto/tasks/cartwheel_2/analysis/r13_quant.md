# Round 13 - quantitative report (step 1, before any diagnosis)

run `2026-11-02_03-53-24_cw2auto_r13`, best checkpoint `model_13999.pt` (score 5.823), evaluated: model_13000.pt 5.778, model_13500.pt 5.684, model_13999.pt 5.823

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 261.2 | 256.0 | +5.2 |
| robot_max_rotation_deg | 263.4 | 257.9 | +5.5 |
| robot_peak_pelvis_m | 0.759 | 0.778 | -0.019 |
| robot_airborne_s | 0.2 | 0.2 | +0 |
| landed_upright | True | True |  |
| end_tilt_deg | 15.9 | 14.4 | +1.5 |
| pelvis_rise_m | 0.012 | 0.052 | -0.04 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.621 | 0.616 | +0.005 |
| track_body_err_m | 0.0443 | 0.0479 | -0.0036 |
| track_joint_err | 0.6018 | 0.5884 | +0.0134 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 4.0 | 5.5 | -1.5 |
| post_drift_m | 0.0 | 0.0 | +0 |
| post_sway_m | 0.0 | 0.0 | +0 |
| post_pelvis_speed_max | 0.0 | 0.0 | +0 |
| post_action_change | 0.0001 | 0.0 | +0.0001 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 3.9 | 5.5 | -1.6 |
| hold_height_err_m | 0.02 | 0.015 | +0.005 |
| hold_pose_err_rad | 0.054 | 0.052 | +0.002 |
| hold_pelvis_speed_max | 0.0 | 0.0 | +0 |
| hold_drift_m | 0.0 | 0.0 | +0 |
| hold_sway_m | 0.0 | 0.0 | +0 |
| hold_torso_angvel_rms | 0.003 | 0.0 | +0.003 |
| hold_action_change | 0.0001 | 0.0 | +0.0001 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.823 | 5.808 | +0.015 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_03-53-24_cw2auto_r13/eval/_post_auto_model_13999.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.718 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-02_03-53-24_cw2auto_r13/eval/flip_auto_model_13999.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.996 | 0.996 | 0.0 | [258.7, 266.8, 275.2] | [11.2, 14.4, 18.2] | [0.0, 0.0, 0.002] |
| dr | 0.992 | 0.887 | 0.0 | [255.9, 270.5, 285.6] | [14.7, 18.7, 22.9] | [0.022, 0.122, 0.412] |
| delay1 | 0.895 | 0.727 | 0.016 | [259.4, 275.1, 291.3] | [15.5, 20.6, 25.7] | [0.029, 0.166, 0.644] |
| delay2 | 0.414 | 0.199 | 0.137 | [248.1, 282.1, 386.4] | [19.0, 25.3, 111.3] | [0.116, 0.507, 1.233] |
| kp085 | 0.984 | 0.891 | 0.0 | [261.0, 275.7, 291.1] | [15.2, 19.4, 24.5] | [0.022, 0.106, 0.376] |

## A3. Segment probe `13999` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 1.0 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 1.0 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 12 of 53 measurements beyond tolerance

- 4.3 asymmetry:wrist_roll - left/right differ 44 deg vs reference 1 deg
- 3.0 asymmetry:shoulder_yaw - left/right differ 31 deg vs reference 1 deg
- 2.6 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 46 vs reference 1 rad/s^2
- 1.8 joint:wrist_roll - left_wrist_roll_joint: mean |err| 27 deg (signed +27), step 8: robot +0.55 vs ref -0.02 rad
- 1.5 joint:knee - left_knee_joint: mean |err| 23 deg (signed +23), step 15: robot +0.63 vs ref +0.06 rad
- 1.5 asymmetry:hip_roll - left/right differ 25 deg vs reference 10 deg

**lunge**: 10 of 51 measurements beyond tolerance

- 2.6 asymmetry:shoulder_yaw - left/right differ 35 deg vs reference 10 deg
- 2.5 asymmetry:wrist_roll - left/right differ 35 deg vs reference 10 deg
- 1.9 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 32 vs reference 1 rad/s^2
- 1.8 body:wrist_yaw - left_wrist_yaw_link: mean 0.14 m, max 0.19 m
- 1.6 body:elbow - left_elbow_link: mean 0.12 m, max 0.16 m
- 1.6 body:ankle_roll - left_ankle_roll_link: mean 0.12 m, max 0.15 m

**support**: 15 of 51 measurements beyond tolerance

- 2.0 body:ankle_roll - right_ankle_roll_link: mean 0.16 m, max 0.41 m
- 2.0 joint:wrist_roll - left_wrist_roll_joint: mean |err| 30 deg (signed +12), step 63: robot +1.18 vs ref +0.25 rad
- 1.8 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.22 m
- 1.7 asymmetry:wrist_roll - left/right differ 32 deg vs reference 16 deg
- 1.5 asymmetry:hip_yaw - left/right differ 29 deg vs reference 14 deg
- 1.3 joint:hip_roll - left_hip_roll_joint: mean |err| 19 deg (signed -19), step 68: robot +0.27 vs ref +0.93 rad

**land**: 18 of 53 measurements beyond tolerance

- 4.2 body:ankle_roll - left_ankle_roll_link: mean 0.33 m, max 0.46 m
- 3.1 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 54 vs reference 1 rad/s^2
- 3.1 body:knee - left_knee_link: mean 0.24 m, max 0.31 m
- 2.7 contact:right_foot - right_foot off the floor for 8 of 14 steps the reference has it down
- 2.6 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 41 vs reference 0 rad/s^2
- 2.6 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 39 deg (signed +39), step 84: robot +0.24 vs ref -0.80 rad

**settle**: 7 of 54 measurements beyond tolerance

- 3.3 jitter:all - mean action change 0.166 (quiet < 0.05)
- 2.0 body:ankle_roll - left_ankle_roll_link: mean 0.16 m, max 0.23 m
- 1.7 asymmetry:wrist_roll - left/right differ 23 deg vs reference 6 deg
- 1.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.11 m, max 0.16 m
- 1.1 joint:hip_roll - right_hip_roll_joint: mean |err| 17 deg (signed +17), step 102: robot -0.24 vs ref -0.69 rad
- 1.1 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 31 vs reference 4 rad/s^2

**stand_after**: 1 of 54 measurements beyond tolerance

- 1.1 body:ankle_roll - right_ankle_roll_link: mean 0.09 m, max 0.10 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 3.0 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.0741 |
| 4.3 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.0234 |
| 1.3 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.319 |
| 1.6 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.289 |
| 1.8 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.245 |
| 1.1 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.406 |
| 2.6 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.106 |
| 2.5 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.11 |
| 1.0 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.401 |
| 1.3 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.328 |
| 1.2 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.366 |
| 1.1 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.383 |
| 1.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.377 |
| 2.0 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.18 |
| 2.0 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.196 |
| 1.8 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.244 |
| 1.2 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.377 |
| 2.6 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.105 |
| 1.2 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.359 |
| 4.2 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0358 |
| 1.3 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.358 |
| 3.1 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.0867 |
| 2.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.7 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.232 |
| 3.3 | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.3 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 0.342 |
| 2.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.205 |
| 1.1 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.377 |
| 1.1 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.403 |
| 1.0 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.411 |
| 2.6 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.6 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 3.1 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 1.2 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.369 |
| 1.9 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.7 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.226 |
| 1.5 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.264 |
| 1.5 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.5 | 0.596 |
| 1.1 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.345 |
| 2.0 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.178 |
| 1.9 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.358 |
| 1.7 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.6 | 0.616 |
| 1.3 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.333 |

45 of 107 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.29| rad (end -0.12), reference max |0.51|
- arm joints mean |err| 3 deg; worst: right_elbow 6, left_elbow 4, right_shoulder_yaw 4, right_shoulder_roll 2
- action change mean 0.012 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 4, right_knee 4, right_hip_roll 2, right_ankle_roll 2
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.61 m/s, last 0.43; drift 0.07 m
- settle (steps 95-114): pelvis speed mean 0.23 m/s, last 0.20; drift 0.07 m
- stand_after (steps 115-489): pelvis speed mean 0.01 m/s, last 0.00; drift 0.08 m

## F. Training-config audit (what the training actually ran)

- 32 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 3, decider terms: 2

## F2. Knobs this round trained with vs round 12 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r12: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7ff9dd67fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r13: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7f937711bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r12: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_all_settle', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 2.0), ('lib_cartwheel_2_asymmetry_hip_yaw_support', 1.0), ('lib_cartwheel_2_asymmetry_wrist_roll_support', 1.0), ('agent_r
  r13: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_all_settle', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.1462, 0.0752]), rounds used 13, GPU 20.7 h, over budget: False, waivers in force: 2

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.0 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.0 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.0 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.003 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.0 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 3.9 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.054 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.02 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.0 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 4.0 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 4.31 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.992 | >= 0.95 | pass |
| robust_latency_20ms | robust.delay1 | 0.895 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.984 | >= 0.95 | pass |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 261.2 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/asymmetry:wrist_roll:stand

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
- [ ] sheet_480-519.jpg
- [ ] sheet_520-559.jpg
- [ ] sheet_560-599.jpg
- [ ] sheet_600-639.jpg
- [ ] sheet_640-679.jpg
- [ ] sheet_680-719.jpg
- [ ] sheet_720-737.jpg
