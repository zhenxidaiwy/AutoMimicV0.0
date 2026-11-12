# Round 7 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_08-05-57_cw2auto_r07`, best checkpoint `model_8500.pt` (score 5.842), evaluated: model_8000.pt 5.763, model_8500.pt 5.842, model_8994.pt 5.821

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 9.8 | +5 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 261.0 | 252.5 | +8.5 |
| robot_max_rotation_deg | 261.1 | 253.1 | +8 |
| robot_peak_pelvis_m | 0.772 | 0.77 | +0.002 |
| robot_airborne_s | 0.22 | 0.2 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 17.6 | 12.2 | +5.4 |
| pelvis_rise_m | 0.05 | 0.043 | +0.007 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.627 | 0.635 | -0.008 |
| track_body_err_m | 0.0395 | 0.0641 | -0.0246 |
| track_joint_err | 0.5488 | 0.8898 | -0.341 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 2.2 | 7.7 | -5.5 |
| post_drift_m | 0.0 | 0.0 | +0 |
| post_sway_m | 0.0 | 0.001 | -0.001 |
| post_pelvis_speed_max | 0.0 | 0.005 | -0.005 |
| post_action_change | 0.0 | 0.0002 | -0.0002 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 2.2 | 9.4 | -7.2 |
| hold_height_err_m | 0.01 | 0.029 | -0.019 |
| hold_pose_err_rad | 0.049 | 0.081 | -0.032 |
| hold_pelvis_speed_max | 0.0 | 0.106 | -0.106 |
| hold_drift_m | 0.0 | 0.027 | -0.027 |
| hold_sway_m | 0.0 | 0.025 | -0.025 |
| hold_torso_angvel_rms | 0.0 | 0.077 | -0.077 |
| hold_action_change | 0.0001 | 0.0034 | -0.0033 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.842 | 5.72 | +0.122 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_08-05-57_cw2auto_r07/eval/_post_auto_model_8500.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.709 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_08-05-57_cw2auto_r07/eval/flip_auto_model_8500.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [252.5, 262.2, 275.7] | [14.2, 17.4, 19.7] |
| dr | 0.848 | 0.0 | [240.6, 257.6, 271.5] | [15.3, 18.4, 21.9] |
| delay1 | 0.641 | 0.047 | [234.2, 258.2, 279.9] | [16.1, 20.2, 27.2] |
| delay2 | 0.188 | 0.285 | [212.1, 261.2, 470.7] | [18.9, 24.9, 123.5] |
| kp085 | 0.793 | 0.004 | [247.1, 268.6, 286.0] | [15.1, 20.0, 24.7] |

## A3. Segment probe `8994` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

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

**stand**: 13 of 53 measurements beyond tolerance

- 3.0 asymmetry:wrist_roll - left/right differ 31 deg vs reference 1 deg
- 2.3 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 44 vs reference 1 rad/s^2
- 1.8 asymmetry:elbow - left/right differ 25 deg vs reference 6 deg
- 1.7 joint:knee - left_knee_joint: mean |err| 25 deg (signed +25), step 15: robot +0.74 vs ref +0.06 rad
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.13 m, max 0.20 m
- 1.6 joint:wrist_roll - left_wrist_roll_joint: mean |err| 24 deg (signed -24), step 6: robot -0.53 vs ref -0.02 rad

**lunge**: 5 of 51 measurements beyond tolerance

- 1.6 body:wrist_yaw - left_wrist_yaw_link: mean 0.13 m, max 0.22 m
- 1.4 body:ankle_roll - left_ankle_roll_link: mean 0.11 m, max 0.16 m
- 1.2 joint:knee - left_knee_joint: mean |err| 18 deg (signed +13), step 19: robot +0.84 vs ref +0.08 rad
- 1.1 body:elbow - left_elbow_link: mean 0.08 m, max 0.15 m
- 1.0 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 15 deg (signed -3), step 18: robot -0.22 vs ref +0.36 rad

**support**: 14 of 51 measurements beyond tolerance

- 3.1 asymmetry:hip_yaw - left/right differ 45 deg vs reference 14 deg
- 2.3 body:ankle_roll - right_ankle_roll_link: mean 0.18 m, max 0.41 m
- 2.0 joint:wrist_roll - right_wrist_roll_joint: mean |err| 30 deg (signed -23), step 69: robot -1.07 vs ref -0.21 rad
- 1.9 asymmetry:shoulder_yaw - left/right differ 38 deg vs reference 19 deg
- 1.8 body:knee - right_knee_link: mean 0.14 m, max 0.26 m
- 1.7 joint:hip_yaw - left_hip_yaw_joint: mean |err| 26 deg (signed -16), step 54: robot -1.37 vs ref -0.05 rad

**land**: 17 of 53 measurements beyond tolerance

- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.26 m, max 0.40 m
- 3.1 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 48 vs reference 0 rad/s^2
- 3.0 contact:right_foot - right_foot off the floor for 9 of 14 steps the reference has it down
- 2.7 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 41 deg (signed +41), step 84: robot +0.31 vs ref -0.80 rad
- 2.4 body:knee - left_knee_link: mean 0.19 m, max 0.27 m
- 2.2 joint:hip_pitch - left_hip_pitch_joint: mean |err| 33 deg (signed -33), step 84: robot -0.99 vs ref -0.11 rad

**settle**: 4 of 54 measurements beyond tolerance

- 2.0 body:ankle_roll - left_ankle_roll_link: mean 0.16 m, max 0.17 m
- 1.9 jitter:all - mean action change 0.096 (quiet < 0.05)
- 1.2 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 18 deg (signed +14), step 95: robot -0.11 vs ref -0.62 rad
- 1.1 body:knee - left_knee_link: mean 0.09 m, max 0.10 m

**stand_after**: 0 of 54 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.3 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.308 |
| 1.8 | cartwheel_2/asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.203 |
| 3.0 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.0739 |
| 1.0 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.412 |
| 1.2 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.347 |
| 1.4 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.336 |
| 1.6 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.27 |
| 1.2 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.355 |
| 1.1 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.372 |
| 1.7 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.222 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.363 |
| 1.3 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.315 |
| 2.0 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.175 |
| 2.3 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.161 |
| 1.5 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.302 |
| 1.8 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.242 |
| 2.7 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0934 |
| 3.2 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0753 |
| 1.6 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.289 |
| 2.4 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.15 |
| 1.3 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.319 |
| 3.0 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.2 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.346 |
| 1.9 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.199 |
| 1.2 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.358 |
| 1.4 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.282 |
| 3.1 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.3 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.7 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.396 |
| 1.4 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.297 |
| 1.7 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.237 |
| 1.5 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.306 |
| 1.7 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.267 |
| 3.1 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.0646 |
| 1.2 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.3 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.33 |
| 2.2 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.15 |

39 of 102 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.30| rad (end -0.19), reference max |0.51|
- arm joints mean |err| 3 deg; worst: right_shoulder_yaw 6, right_shoulder_pitch 5, left_shoulder_pitch 4, left_shoulder_yaw 4
- action change mean 0.011 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_hip_yaw 3, right_ankle_pitch 3, left_ankle_pitch 3, right_wrist_roll 2
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.55 m/s, last 0.06; drift 0.07 m
- settle (steps 95-114): pelvis speed mean 0.16 m/s, last 0.13; drift 0.06 m
- stand_after (steps 115-489): pelvis speed mean 0.02 m/s, last 0.00; drift 0.09 m

## F. Training-config audit (what the training actually ran)

- 29 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 1, decider terms: 1

## F2. Knobs this round trained with vs round 6 (3 differences)

- prior.land: 3.0 -> 1.0
- reference.labels: "labels_hold_50fps.npz" -> "labels_hold8_50fps.npz"
- reference.variant: "reachqp_vlm_hold" -> "reachqp_vlm_hold8"

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r6: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7c91f067bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r7: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x717760b07d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [-0.0995, 0.3838]), rounds used 7, GPU 11.1 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.0 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.0 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.0 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.0 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.0 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 2.2 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.049 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.01 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.0 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 2.2 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 3.23 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.848 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.641 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.793 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 261.0 | >= 229.95000000000002 | pass |
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
