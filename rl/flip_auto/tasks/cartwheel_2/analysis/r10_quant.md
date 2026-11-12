# Round 10 - quantitative report (step 1, before any diagnosis)

run `2026-10-28_15-30-50_cw2auto_r10`, best checkpoint `model_13491.pt` (score 5.793), evaluated: model_12500.pt 5.779, model_13000.pt 5.778, model_13491.pt 5.793

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 261.7 | 263.2 | -1.5 |
| robot_max_rotation_deg | 261.9 | 264.9 | -3 |
| robot_peak_pelvis_m | 0.767 | 0.774 | -0.007 |
| robot_airborne_s | 0.2 | 0.22 | -0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 13.3 | 13.7 | -0.4 |
| pelvis_rise_m | 0.046 | 0.039 | +0.007 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.625 | 0.63 | -0.005 |
| track_body_err_m | 0.0517 | 0.0618 | -0.0101 |
| track_joint_err | 0.6344 | 0.6552 | -0.0208 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 6.6 | 6.2 | +0.4 |
| post_drift_m | 0.0 | 0.001 | -0.001 |
| post_sway_m | 0.0 | 0.001 | -0.001 |
| post_pelvis_speed_max | 0.0 | 0.002 | -0.002 |
| post_action_change | 0.0 | 0.0005 | -0.0005 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 6.7 | 6.1 | +0.6 |
| hold_height_err_m | 0.018 | 0.022 | -0.004 |
| hold_pose_err_rad | 0.054 | 0.072 | -0.018 |
| hold_pelvis_speed_max | 0.0 | 0.004 | -0.004 |
| hold_drift_m | 0.0 | 0.002 | -0.002 |
| hold_sway_m | 0.0 | 0.001 | -0.001 |
| hold_torso_angvel_rms | 0.001 | 0.009 | -0.008 |
| hold_action_change | 0.0001 | 0.0009 | -0.0008 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.793 | 5.753 | +0.04 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-28_15-30-50_cw2auto_r10/eval/_post_auto_model_13491.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.717 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-28_15-30-50_cw2auto_r10/eval/flip_auto_model_13491.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.965 | 0.965 | 0.0 | [233.0, 248.7, 257.9] | [11.4, 15.6, 19.5] | [0.0, 0.001, 0.002] |
| dr | 0.879 | 0.82 | 0.004 | [226.3, 243.0, 259.3] | [15.2, 19.1, 23.9] | [0.02, 0.089, 0.366] |
| delay1 | 0.707 | 0.59 | 0.012 | [216.0, 238.5, 258.4] | [17.4, 21.8, 26.7] | [0.029, 0.153, 0.525] |
| delay2 | 0.445 | 0.301 | 0.086 | [213.0, 237.2, 281.6] | [21.7, 27.5, 107.1] | [0.069, 0.336, 0.96] |
| kp085 | 0.871 | 0.809 | 0.0 | [223.4, 244.6, 265.6] | [16.1, 21.7, 26.0] | [0.017, 0.121, 0.449] |

## A3. Segment probe `13491` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 0.953 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 1.0 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 20 of 53 measurements beyond tolerance

- 2.5 joint:knee - left_knee_joint: mean |err| 37 deg (signed +37), step 15: robot +0.94 vs ref +0.06 rad
- 2.2 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 32 deg (signed -32), step 15: robot -0.34 vs ref +0.46 rad
- 2.1 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 42 vs reference 1 rad/s^2
- 2.1 asymmetry:wrist_roll - left/right differ 22 deg vs reference 1 deg
- 2.1 body:wrist_yaw - right_wrist_yaw_link: mean 0.17 m, max 0.33 m
- 1.6 asymmetry:hip_yaw - left/right differ 21 deg vs reference 5 deg

**lunge**: 14 of 51 measurements beyond tolerance

- 2.9 body:wrist_yaw - right_wrist_yaw_link: mean 0.23 m, max 0.36 m
- 2.5 asymmetry:shoulder_yaw - left/right differ 35 deg vs reference 10 deg
- 2.2 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 39 vs reference 1 rad/s^2
- 1.7 body:elbow - right_elbow_link: mean 0.13 m, max 0.22 m
- 1.6 asymmetry:shoulder_roll - left/right differ 32 deg vs reference 16 deg
- 1.5 body:ankle_roll - left_ankle_roll_link: mean 0.12 m, max 0.19 m

**support**: 16 of 51 measurements beyond tolerance

- 2.9 asymmetry:hip_yaw - left/right differ 42 deg vs reference 14 deg
- 2.2 asymmetry:shoulder_yaw - left/right differ 41 deg vs reference 19 deg
- 2.1 asymmetry:hip_pitch - left/right differ 89 deg vs reference 68 deg
- 2.0 body:ankle_roll - right_ankle_roll_link: mean 0.16 m, max 0.47 m
- 2.0 joint:wrist_roll - left_wrist_roll_joint: mean |err| 29 deg (signed +20), step 63: robot +1.30 vs ref +0.25 rad
- 1.5 joint:elbow - left_elbow_joint: mean |err| 22 deg (signed -19), step 68: robot +0.57 vs ref +1.32 rad

**land**: 18 of 53 measurements beyond tolerance

- 3.4 body:ankle_roll - left_ankle_roll_link: mean 0.28 m, max 0.38 m
- 2.8 body:knee - left_knee_link: mean 0.23 m, max 0.29 m
- 2.7 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 41 deg (signed +41), step 84: robot +0.21 vs ref -0.80 rad
- 2.7 contact:right_foot - right_foot off the floor for 8 of 14 steps the reference has it down
- 2.6 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 41 vs reference 0 rad/s^2
- 2.3 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 40 vs reference 1 rad/s^2

**settle**: 5 of 54 measurements beyond tolerance

- 2.0 body:ankle_roll - left_ankle_roll_link: mean 0.16 m, max 0.22 m
- 1.4 jitter:all - mean action change 0.069 (quiet < 0.05)
- 1.3 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 20 deg (signed +18), step 97: robot -0.11 vs ref -0.62 rad
- 1.2 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 28 vs reference 3 rad/s^2
- 1.2 body:knee - left_knee_link: mean 0.09 m, max 0.15 m

**stand_after**: 1 of 54 measurements beyond tolerance

- 1.1 body:wrist_yaw - right_wrist_yaw_link: mean 0.09 m, max 0.11 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.5 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.282 |
| 1.6 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.252 |
| 2.1 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.157 |
| 1.5 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.276 |
| 1.2 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.336 |
| 1.3 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.317 |
| 1.5 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.293 |
| 2.9 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.101 |
| 2.5 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.108 |
| 1.0 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.406 |
| 1.1 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.397 |
| 1.2 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.343 |
| 1.0 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.401 |
| 1.4 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.298 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.342 |
| 1.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.372 |
| 2.0 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.181 |
| 2.0 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.195 |
| 1.3 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.345 |
| 1.4 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.324 |
| 2.7 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0934 |
| 1.5 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.26 |
| 3.4 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0634 |
| 1.5 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.31 |
| 2.8 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.104 |
| 2.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.3 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.309 |
| 1.4 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 0.418 |
| 2.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.206 |
| 1.5 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.279 |
| 2.6 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.1 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.3 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 1.1 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.401 |
| 2.2 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.388 |
| 2.5 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.113 |
| 1.2 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.369 |
| 2.1 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.189 |
| 2.9 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.082 |
| 1.2 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.1 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.162 |
| 1.3 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.332 |
| 2.2 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.151 |
| 1.4 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.2 | 0.302 |
| 2.2 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.152 |

47 of 106 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.23| rad (end -0.18), reference max |0.51|
- arm joints mean |err| 2 deg; worst: right_shoulder_roll 4, right_shoulder_pitch 4, right_elbow 3, left_shoulder_yaw 3
- action change mean 0.007 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_wrist_roll 1, right_wrist_roll 1, left_elbow 1, right_elbow 1
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.55 m/s, last 0.07; drift 0.07 m
- settle (steps 95-114): pelvis speed mean 0.27 m/s, last 0.17; drift 0.11 m
- stand_after (steps 115-489): pelvis speed mean 0.01 m/s, last 0.00; drift 0.05 m

## F. Training-config audit (what the training actually ran)

- 32 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 2, decider terms: 3

## F2. Knobs this round trained with vs round 9 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r9: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7108e6973d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r10: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x73404651bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r9: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0)]
  r10: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('lib_cartwheel_2_jitter_wrist_roll_land', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0), ('agent_r10_hold_posture', 1.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [-0.545, 0.1634]), rounds used 10, GPU 15.9 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.0 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.0 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.0 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.001 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.0 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 6.7 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.054 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.018 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.0 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 6.6 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 3.45 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.879 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.707 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.871 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 261.7 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/body:ankle_roll:land

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
