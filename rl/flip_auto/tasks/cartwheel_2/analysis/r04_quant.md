# Round 4 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_02-43-10_cw2auto_r04`, best checkpoint `model_3500.pt` (score 5.704), evaluated: model_3500.pt 5.704, model_4000.pt 5.683, model_4497.pt 5.691

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 259.1 | 254.5 | +4.6 |
| robot_max_rotation_deg | 259.1 | 255.7 | +3.4 |
| robot_peak_pelvis_m | 0.777 | 0.774 | +0.003 |
| robot_airborne_s | 0.22 | 0.24 | -0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 14.5 | 15.8 | -1.3 |
| pelvis_rise_m | 0.053 | 0.014 | +0.039 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.554 | 0.567 | -0.013 |
| track_body_err_m | 0.0739 | 0.0875 | -0.0136 |
| track_joint_err | 0.9576 | 1.175 | -0.217 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 5.3 | 4.5 | +0.8 |
| post_drift_m | 0.016 | 0.007 | +0.009 |
| post_sway_m | 0.012 | 0.004 | +0.008 |
| post_pelvis_speed_max | 0.023 | 0.021 | +0.002 |
| post_action_change | 0.001 | 0.0008 | +0.0002 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 5.5 | 5.3 | +0.2 |
| hold_height_err_m | 0.038 | 0.032 | +0.006 |
| hold_pose_err_rad | 0.076 | 0.098 | -0.022 |
| hold_pelvis_speed_max | 0.213 | 0.326 | -0.113 |
| hold_drift_m | 0.061 | 0.039 | +0.022 |
| hold_sway_m | 0.056 | 0.041 | +0.015 |
| hold_torso_angvel_rms | 0.146 | 0.19 | -0.044 |
| hold_action_change | 0.0097 | 0.0125 | -0.0028 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.704 | 5.642 | +0.062 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_02-43-10_cw2auto_r04/eval/_post_auto_model_3500.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.726 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_02-43-10_cw2auto_r04/eval/flip_auto_model_3500.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 0.988 | 0.004 | [250.7, 267.0, 279.3] | [15.0, 17.4, 20.8] |
| dr | 0.762 | 0.012 | [236.0, 257.7, 274.5] | [16.7, 19.7, 22.6] |
| delay1 | 0.453 | 0.086 | [223.1, 261.1, 278.1] | [17.9, 21.3, 109.5] |
| delay2 | 0.133 | 0.48 | [155.5, 264.9, 420.5] | [22.2, 43.3, 139.3] |
| kp085 | 0.66 | 0.004 | [228.0, 261.9, 283.2] | [17.2, 20.4, 25.0] |

## A3. Segment probe `4497` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [218, 238, 238] | 238 | stand | 0.844 |
| 16 | lunge | [222, 222, 222] | 238 | stand | 0.938 |
| 30 | lunge | [208, 208, 208] | 238 | stand | 0.984 |
| 46 | support | [192, 192, 192] | 238 | stand | 0.953 |
| 60 | support | [155, 178, 178] | 238 | stand | 0.859 |
| 81 | land | [18, 89, 157] | 170 | stand | 0.359 |
| 95 | settle | [143, 143, 143] | 238 | stand | 0.984 |
| 115 | stand | [123, 123, 123] | 238 | stand | 0.969 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 21 of 53 measurements beyond tolerance

- 4.7 contact:left_foot - left_foot off the floor for 14 of 16 steps
- 3.9 asymmetry:wrist_roll - left/right differ 40 deg vs reference 1 deg
- 2.3 body:knee - left_knee_link: mean 0.18 m, max 0.24 m
- 2.2 joint:knee - left_knee_joint: mean |err| 34 deg (signed +34), step 15: robot +0.82 vs ref +0.06 rad
- 2.2 body:ankle_roll - left_ankle_roll_link: mean 0.17 m, max 0.23 m
- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.23 m

**lunge**: 11 of 51 measurements beyond tolerance

- 2.5 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 44 vs reference 1 rad/s^2
- 2.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.19 m, max 0.28 m
- 2.1 joint:wrist_roll - right_wrist_roll_joint: mean |err| 32 deg (signed -32), step 31: robot -0.72 vs ref -0.01 rad
- 1.8 asymmetry:wrist_roll - left/right differ 28 deg vs reference 10 deg
- 1.6 body:ankle_roll - left_ankle_roll_link: mean 0.13 m, max 0.17 m
- 1.5 body:knee - right_knee_link: mean 0.12 m, max 0.19 m

**support**: 11 of 51 measurements beyond tolerance

- 2.6 joint:wrist_roll - right_wrist_roll_joint: mean |err| 39 deg (signed -24), step 52: robot -1.37 vs ref -0.32 rad
- 2.4 body:ankle_roll - right_ankle_roll_link: mean 0.19 m, max 0.33 m
- 1.8 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.19 m
- 1.6 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 24 deg (signed -19), step 71: robot -0.71 vs ref -0.04 rad
- 1.5 joint:hip_yaw - left_hip_yaw_joint: mean |err| 23 deg (signed -5), step 51: robot -1.20 vs ref -0.15 rad
- 1.4 joint:hip_roll - left_hip_roll_joint: mean |err| 22 deg (signed -22), step 68: robot +0.13 vs ref +0.93 rad

**land**: 26 of 53 measurements beyond tolerance

- 4.2 body:ankle_roll - left_ankle_roll_link: mean 0.34 m, max 0.48 m
- 3.7 contact:left_foot - left_foot off the floor for 11 of 14 steps
- 3.2 body:knee - left_knee_link: mean 0.26 m, max 0.33 m
- 2.7 contact:right_foot - right_foot off the floor for 8 of 14 steps
- 2.6 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 39 deg (signed +39), step 83: robot +0.26 vs ref -0.79 rad
- 2.4 asymmetry:shoulder_yaw - left/right differ 56 deg vs reference 32 deg

**settle**: 4 of 54 measurements beyond tolerance

- 2.8 body:ankle_roll - left_ankle_roll_link: mean 0.22 m, max 0.26 m
- 2.5 jitter:all - mean action change 0.124 (quiet < 0.05)
- 1.4 body:knee - left_knee_link: mean 0.11 m, max 0.15 m
- 1.1 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 16 deg (signed +3), step 114: robot -0.16 vs ref +0.47 rad

**stand_after**: 2 of 54 measurements beyond tolerance

- 1.3 body:ankle_roll - right_ankle_roll_link: mean 0.10 m, max 0.17 m
- 1.1 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 16 deg (signed -16), step 115: robot -0.16 vs ref +0.47 rad

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.3 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.33 |
| 1.4 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.301 |
| 3.9 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.0339 |
| 4.7 | cartwheel_2/contact:left_foot:stand | dyn_contact | 0.0 | None | - |
| 1.2 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.344 |
| 2.1 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.153 |
| 1.6 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.27 |
| 2.3 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.156 |
| 1.5 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.297 |
| 1.8 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.204 |
| 1.6 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.244 |
| 1.4 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.284 |
| 1.5 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.267 |
| 1.1 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.38 |
| 2.6 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.101 |
| 2.4 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.147 |
| 1.8 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.246 |
| 1.3 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.361 |
| 2.6 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.102 |
| 4.2 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0343 |
| 1.8 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.229 |
| 3.2 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.0758 |
| 2.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.1 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.395 |
| 2.5 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 2.8 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.109 |
| 1.1 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.395 |
| 1.3 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.352 |
| 3.7 | cartwheel_2/contact:left_foot:land | dyn_contact | 0.0 | None | - |
| 1.8 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.9 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.0 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.3 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.353 |
| 2.5 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 2.4 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.119 |
| 2.3 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.162 |
| 2.2 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.141 |
| 2.2 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.176 |
| 2.0 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.196 |

39 of 98 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 1

- 2.0 jitter:shoulder_yaw:land - left_shoulder_yaw_joint: joint acceleration RMS 65 vs reference 6 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.27| rad (end -0.16), reference max |0.51|
- arm joints mean |err| 3 deg; worst: left_shoulder_yaw 4, left_shoulder_roll 4, right_shoulder_pitch 3, right_shoulder_roll 3
- action change mean 0.034 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_knee 7, left_ankle_pitch 5, right_hip_yaw 5, right_ankle_pitch 5
- feet off the floor (> 6 cm): left 2, right 0 of 145 steps
- land (steps 81-94): pelvis speed mean 0.60 m/s, last 0.14; drift 0.07 m
- settle (steps 95-114): pelvis speed mean 0.13 m/s, last 0.19; drift 0.03 m
- stand_after (steps 115-239): pelvis speed mean 0.08 m/s, last 0.02; drift 0.12 m

## F. Training-config audit (what the training actually ran)

- 27 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}}
- active library fixes: 0, decider terms: 0

## F2. Knobs this round trained with vs round 3 (2 differences)

- terms.term_below_reference.margin: - -> 0.12
- terms.term_below_reference.min_clear: - -> 0.05

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r3: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x73e88547bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r4: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7ecbae107d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] flip terminations: r3: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
  r4: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}}

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.8737, 0.1554]), rounds used 4, GPU 6.3 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.213 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.061 | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | 0.056 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.146 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.01 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 5.5 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.076 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.038 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.016 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 5.3 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 4.67 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.762 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.453 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.66 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 259.1 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/contact:left_foot:stand

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
