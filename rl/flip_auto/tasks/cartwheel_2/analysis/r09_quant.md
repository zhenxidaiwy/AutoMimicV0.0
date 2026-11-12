# Round 9 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_18-51-42_cw2auto_r09`, best checkpoint `model_11992.pt` (score 5.753), evaluated: model_11000.pt 5.664, model_11500.pt 5.73, model_11992.pt 5.753

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 14.8 | 14.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 263.2 | 264.3 | -1.1 |
| robot_max_rotation_deg | 264.9 | 265.7 | -0.8 |
| robot_peak_pelvis_m | 0.774 | 0.774 | +0 |
| robot_airborne_s | 0.22 | 0.2 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 13.7 | 17.3 | -3.6 |
| pelvis_rise_m | 0.039 | 0.027 | +0.012 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.63 | 0.629 | +0.001 |
| track_body_err_m | 0.0618 | 0.04 | +0.0218 |
| track_joint_err | 0.6552 | 0.6112 | +0.044 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 6.2 | 2.6 | +3.6 |
| post_drift_m | 0.001 | 0.003 | -0.002 |
| post_sway_m | 0.001 | 0.002 | -0.001 |
| post_pelvis_speed_max | 0.002 | 0.001 | +0.001 |
| post_action_change | 0.0005 | 0.0001 | +0.0004 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 6.1 | 2.5 | +3.6 |
| hold_height_err_m | 0.022 | 0.016 | +0.006 |
| hold_pose_err_rad | 0.072 | 0.058 | +0.014 |
| hold_pelvis_speed_max | 0.004 | 0.002 | +0.002 |
| hold_drift_m | 0.002 | 0.002 | +0 |
| hold_sway_m | 0.001 | 0.001 | +0 |
| hold_torso_angvel_rms | 0.009 | 0.001 | +0.008 |
| hold_action_change | 0.0009 | 0.0002 | +0.0007 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.753 | 5.84 | -0.087 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_18-51-42_cw2auto_r09/eval/_post_auto_model_11992.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.719 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_18-51-42_cw2auto_r09/eval/flip_auto_model_11992.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 1.0 | 1.0 | 0.0 | [248.4, 259.2, 269.9] | [11.6, 14.6, 17.1] | [0.0, 0.001, 0.003] |
| dr | 0.992 | 0.957 | 0.0 | [246.7, 261.1, 277.3] | [13.8, 17.6, 21.3] | [0.022, 0.097, 0.281] |
| delay1 | 0.941 | 0.762 | 0.016 | [248.6, 264.1, 278.9] | [14.7, 19.4, 24.8] | [0.038, 0.182, 0.521] |
| delay2 | 0.473 | 0.305 | 0.074 | [240.0, 269.0, 317.0] | [17.2, 22.8, 100.1] | [0.088, 0.494, 1.168] |
| kp085 | 0.996 | 0.938 | 0.0 | [254.5, 271.0, 286.3] | [14.6, 19.2, 24.5] | [0.021, 0.098, 0.325] |

## A3. Segment probe `11992` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [488, 488, 488] | 488 | stand | 0.984 |
| 16 | lunge | [472, 472, 472] | 488 | stand | 1.0 |
| 30 | lunge | [458, 458, 458] | 488 | stand | 1.0 |
| 46 | support | [442, 442, 442] | 488 | stand | 1.0 |
| 60 | support | [428, 428, 428] | 488 | stand | 1.0 |
| 81 | land | [407, 407, 407] | 488 | stand | 1.0 |
| 95 | settle | [393, 393, 393] | 488 | stand | 1.0 |
| 115 | stand | [373, 373, 373] | 488 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 8 of 53 measurements beyond tolerance

- 1.7 asymmetry:hip_pitch - left/right differ 44 deg vs reference 27 deg
- 1.6 joint:knee - left_knee_joint: mean |err| 25 deg (signed +25), step 15: robot +0.67 vs ref +0.06 rad
- 1.5 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 22 deg (signed -22), step 15: robot -0.05 vs ref +0.46 rad
- 1.4 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 58 vs reference 9 rad/s^2
- 1.3 body:ankle_roll - left_ankle_roll_link: mean 0.10 m, max 0.21 m
- 1.1 asymmetry:shoulder_pitch - left/right differ 12 deg vs reference 1 deg

**lunge**: 9 of 51 measurements beyond tolerance

- 2.0 asymmetry:wrist_roll - left/right differ 29 deg vs reference 10 deg
- 1.9 body:ankle_roll - left_ankle_roll_link: mean 0.15 m, max 0.23 m
- 1.8 asymmetry:shoulder_yaw - left/right differ 28 deg vs reference 10 deg
- 1.4 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 25 vs reference 1 rad/s^2
- 1.4 asymmetry:shoulder_pitch - left/right differ 25 deg vs reference 12 deg
- 1.2 body:knee - left_knee_link: mean 0.10 m, max 0.12 m

**support**: 18 of 51 measurements beyond tolerance

- 2.5 asymmetry:shoulder_yaw - left/right differ 45 deg vs reference 19 deg
- 2.4 asymmetry:wrist_roll - left/right differ 40 deg vs reference 16 deg
- 2.4 asymmetry:hip_yaw - left/right differ 37 deg vs reference 14 deg
- 2.1 joint:wrist_roll - left_wrist_roll_joint: mean |err| 31 deg (signed +26), step 64: robot +1.34 vs ref +0.24 rad
- 2.1 body:ankle_roll - right_ankle_roll_link: mean 0.17 m, max 0.42 m
- 1.7 body:wrist_yaw - left_wrist_yaw_link: mean 0.14 m, max 0.24 m

**land**: 18 of 53 measurements beyond tolerance

- 5.0 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 85 vs reference 1 rad/s^2
- 3.0 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 96 vs reference 6 rad/s^2
- 3.0 body:ankle_roll - left_ankle_roll_link: mean 0.24 m, max 0.36 m
- 2.9 asymmetry:shoulder_yaw - left/right differ 61 deg vs reference 32 deg
- 2.7 contact:right_foot - right_foot off the floor for 8 of 14 steps the reference has it down
- 2.5 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 38 deg (signed +38), step 83: robot +0.23 vs ref -0.79 rad

**settle**: 5 of 54 measurements beyond tolerance

- 2.2 body:ankle_roll - left_ankle_roll_link: mean 0.17 m, max 0.24 m
- 1.8 jitter:all - mean action change 0.088 (quiet < 0.05)
- 1.3 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 30 vs reference 3 rad/s^2
- 1.3 body:knee - left_knee_link: mean 0.10 m, max 0.13 m
- 1.0 joint:ankle_roll - right_ankle_roll_joint: mean |err| 15 deg (signed -15), step 98: robot -0.10 vs ref +0.26 rad

**stand_after**: 4 of 54 measurements beyond tolerance

- 1.3 body:ankle_roll - right_ankle_roll_link: mean 0.11 m, max 0.11 m
- 1.3 asymmetry:shoulder_roll - left/right differ 15 deg vs reference 3 deg
- 1.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.08 m, max 0.12 m
- 1.0 asymmetry:hip_roll - left/right differ 16 deg vs reference 6 deg

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.0 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.4 |
| 1.1 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.398 |
| 1.1 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.384 |
| 1.9 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.216 |
| 1.2 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.376 |
| 1.2 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.37 |
| 1.8 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.202 |
| 2.0 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.177 |
| 1.6 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.254 |
| 1.0 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.402 |
| 1.1 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.389 |
| 1.7 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.227 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.34 |
| 1.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.382 |
| 2.1 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.165 |
| 1.0 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.406 |
| 2.1 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.192 |
| 1.7 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.253 |
| 1.5 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.308 |
| 2.5 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.11 |
| 1.0 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.408 |
| 3.0 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0901 |
| 1.7 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.258 |
| 2.4 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.148 |
| 2.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.8 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.0 | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.409 |
| 1.3 | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.331 |
| 1.0 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 0.432 |
| 2.2 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.176 |
| 1.0 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.408 |
| 1.3 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.35 |
| 1.5 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.275 |
| 2.4 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 5.0 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.313 |
| 1.4 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.0776 |
| 1.6 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.238 |
| 1.3 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.356 |
| 2.4 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.128 |
| 1.5 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.277 |
| 1.7 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.227 |
| 3.0 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.5 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.11 |
| 2.4 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.2 | 0.122 |

46 of 105 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.23| rad (end -0.10), reference max |0.51|
- arm joints mean |err| 4 deg; worst: left_elbow 9, right_shoulder_roll 7, left_shoulder_roll 5, left_shoulder_yaw 4
- action change mean 0.009 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 3, left_wrist_roll 2, right_wrist_roll 1, right_hip_yaw 1
- feet off the floor (> 6 cm): left 0, right 0 of 395 steps
- land (steps 81-94): pelvis speed mean 0.53 m/s, last 0.22; drift 0.06 m
- settle (steps 95-114): pelvis speed mean 0.26 m/s, last 0.31; drift 0.09 m
- stand_after (steps 115-489): pelvis speed mean 0.02 m/s, last 0.00; drift 0.07 m

## F. Training-config audit (what the training actually ran)

- 30 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 1, decider terms: 2

## F2. Knobs this round trained with vs round 8 (1 differences)

- delay_ms: 25.0 -> 40.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r8: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x74e525c57d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r9: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7108e6973d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r8: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 2.0)]
  r9: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0), ('agent_r08_hold_spot', 4.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: True (rel. improvement of the last rounds [-0.0127, -0.545]), rounds used 9, GPU 14.3 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.004 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.002 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.001 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.009 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.001 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 6.1 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.072 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.022 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.001 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 6.2 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 4.98 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.992 | >= 0.95 | pass |
| robust_latency_20ms | robust.delay1 | 0.941 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.996 | >= 0.95 | pass |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 263.2 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/jitter:wrist_roll:land

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
