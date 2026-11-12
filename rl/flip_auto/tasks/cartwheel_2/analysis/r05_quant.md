# Round 5 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_04-28-42_cw2auto_r05`, best checkpoint `model_5500.pt` (score 5.767), evaluated: model_5000.pt 5.605, model_5500.pt 5.767, model_5996.pt 5.594

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 259.0 | 259.1 | -0.1 |
| robot_max_rotation_deg | 259.1 | 259.1 | +0 |
| robot_peak_pelvis_m | 0.782 | 0.777 | +0.005 |
| robot_airborne_s | 0.24 | 0.22 | +0.02 |
| landed_upright | True | True |  |
| end_tilt_deg | 16.8 | 14.5 | +2.3 |
| pelvis_rise_m | 0.049 | 0.053 | -0.004 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.63 | 0.554 | +0.076 |
| track_body_err_m | 0.0583 | 0.0739 | -0.0156 |
| track_joint_err | 0.8706 | 0.9576 | -0.087 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 3.1 | 5.3 | -2.2 |
| post_drift_m | 0.002 | 0.016 | -0.014 |
| post_sway_m | 0.001 | 0.012 | -0.011 |
| post_pelvis_speed_max | 0.001 | 0.023 | -0.022 |
| post_action_change | 0.0002 | 0.001 | -0.0008 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 4.0 | 5.5 | -1.5 |
| hold_height_err_m | 0.023 | 0.038 | -0.015 |
| hold_pose_err_rad | 0.076 | 0.076 | +0 |
| hold_pelvis_speed_max | 0.085 | 0.213 | -0.128 |
| hold_drift_m | 0.051 | 0.061 | -0.01 |
| hold_sway_m | 0.042 | 0.056 | -0.014 |
| hold_torso_angvel_rms | 0.058 | 0.146 | -0.088 |
| hold_action_change | 0.0029 | 0.0097 | -0.0068 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.767 | 5.704 | +0.063 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_04-28-42_cw2auto_r05/eval/_post_auto_model_5500.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.712 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_04-28-42_cw2auto_r05/eval/flip_auto_model_5500.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [255.8, 266.1, 276.6] | [13.1, 15.5, 17.7] |
| dr | 0.781 | 0.0 | [243.6, 260.8, 275.3] | [14.7, 18.0, 20.8] |
| delay1 | 0.73 | 0.008 | [245.7, 265.1, 283.6] | [16.4, 19.6, 23.5] |
| delay2 | 0.203 | 0.344 | [142.9, 262.7, 401.7] | [18.7, 26.4, 133.2] |
| kp085 | 0.746 | 0.0 | [247.4, 267.4, 283.3] | [14.6, 18.3, 22.7] |

## A3. Segment probe `5996` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [238, 238, 238] | 238 | stand | 0.938 |
| 16 | lunge | [189, 222, 222] | 238 | stand | 0.875 |
| 30 | lunge | [208, 208, 208] | 238 | stand | 0.984 |
| 46 | support | [192, 192, 192] | 238 | stand | 0.969 |
| 60 | support | [178, 178, 178] | 238 | stand | 0.922 |
| 81 | land | [24, 123, 157] | 204 | stand | 0.469 |
| 95 | settle | [143, 143, 143] | 238 | stand | 0.969 |
| 115 | stand | [123, 123, 123] | 238 | stand | 0.984 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 16 of 53 measurements beyond tolerance

- 4.3 contact:left_foot - left_foot off the floor for 13 of 16 steps
- 2.1 jitter:shoulder_yaw - left_shoulder_yaw_joint: joint acceleration RMS 51 vs reference 3 rad/s^2
- 2.0 asymmetry:hip_yaw - left/right differ 25 deg vs reference 5 deg
- 2.0 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 60 vs reference 5 rad/s^2
- 1.9 joint:knee - left_knee_joint: mean |err| 29 deg (signed +29), step 6: robot +0.74 vs ref +0.11 rad
- 1.7 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 30 vs reference 1 rad/s^2

**lunge**: 5 of 51 measurements beyond tolerance

- 1.5 body:ankle_roll - left_ankle_roll_link: mean 0.12 m, max 0.18 m
- 1.3 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 22 vs reference 1 rad/s^2
- 1.1 asymmetry:wrist_roll - left/right differ 21 deg vs reference 10 deg
- 1.1 joint:ankle_pitch - left_ankle_pitch_joint: mean |err| 17 deg (signed +9), step 42: robot -0.39 vs ref -0.87 rad
- 1.1 body:knee - left_knee_link: mean 0.09 m, max 0.10 m

**support**: 13 of 51 measurements beyond tolerance

- 3.5 asymmetry:hip_yaw - left/right differ 48 deg vs reference 14 deg
- 2.7 body:ankle_roll - right_ankle_roll_link: mean 0.21 m, max 0.51 m
- 2.2 joint:wrist_roll - left_wrist_roll_joint: mean |err| 34 deg (signed +33), step 65: robot +1.11 vs ref +0.25 rad
- 1.8 joint:hip_yaw - left_hip_yaw_joint: mean |err| 27 deg (signed -21), step 52: robot -1.68 vs ref -0.15 rad
- 1.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.14 m, max 0.24 m
- 1.6 joint:elbow - left_elbow_joint: mean |err| 25 deg (signed -20), step 64: robot +0.18 vs ref +1.12 rad

**land**: 13 of 53 measurements beyond tolerance

- 4.0 contact:left_foot - left_foot off the floor for 12 of 14 steps
- 3.4 body:ankle_roll - left_ankle_roll_link: mean 0.27 m, max 0.44 m
- 3.0 contact:right_foot - right_foot off the floor for 9 of 14 steps
- 2.9 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 50 vs reference 1 rad/s^2
- 2.5 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 37 deg (signed +37), step 84: robot +0.32 vs ref -0.80 rad
- 2.4 body:knee - left_knee_link: mean 0.19 m, max 0.30 m

**settle**: 4 of 54 measurements beyond tolerance

- 2.0 body:ankle_roll - right_ankle_roll_link: mean 0.16 m, max 0.17 m
- 1.5 asymmetry:knee - left/right differ 29 deg vs reference 14 deg
- 1.5 jitter:all - mean action change 0.074 (quiet < 0.05)
- 1.1 joint:hip_roll - right_hip_roll_joint: mean |err| 16 deg (signed +16), step 95: robot -0.32 vs ref -0.69 rad

**stand_after**: 4 of 54 measurements beyond tolerance

- 1.2 asymmetry:hip_roll - left/right differ 17 deg vs reference 6 deg
- 1.1 asymmetry:wrist_roll - left/right differ 17 deg vs reference 6 deg
- 1.1 body:wrist_yaw - left_wrist_yaw_link: mean 0.09 m, max 0.09 m
- 1.0 body:ankle_roll - right_ankle_roll_link: mean 0.08 m, max 0.16 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.0 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.17 |
| 1.6 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.256 |
| 4.3 | cartwheel_2/contact:left_foot:stand | dyn_contact | 1.0 | None | - |
| 1.1 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.379 |
| 1.5 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.304 |
| 1.1 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.419 |
| 1.1 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.369 |
| 1.1 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.386 |
| 1.3 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.333 |
| 1.8 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.212 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.344 |
| 2.2 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.141 |
| 2.7 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.117 |
| 1.7 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.249 |
| 1.6 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.276 |
| 2.5 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.114 |
| 3.4 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.068 |
| 1.7 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.254 |
| 2.4 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.143 |
| 3.0 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.5 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.358 |
| 1.1 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.367 |
| 1.1 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 0.418 |
| 2.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.21 |
| 1.1 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.383 |
| 1.0 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.443 |
| 1.6 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.239 |
| 4.0 | cartwheel_2/contact:left_foot:land | dyn_contact | 0.0 | None | - |
| 1.8 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.7 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.9 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.4 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.321 |
| 1.3 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.273 |
| 1.9 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.189 |
| 1.6 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.269 |
| 1.2 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.37 |
| 3.5 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.0489 |
| 2.1 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |

40 of 100 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.33| rad (end -0.13), reference max |0.51|
- arm joints mean |err| 3 deg; worst: left_elbow 6, left_shoulder_roll 5, right_elbow 4, left_shoulder_yaw 4
- action change mean 0.017 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 7, right_knee 3, right_hip_roll 3, left_wrist_roll 3
- feet off the floor (> 6 cm): left 0, right 0 of 145 steps
- land (steps 81-94): pelvis speed mean 0.52 m/s, last 0.19; drift 0.03 m
- settle (steps 95-114): pelvis speed mean 0.23 m/s, last 0.31; drift 0.07 m
- stand_after (steps 115-239): pelvis speed mean 0.05 m/s, last 0.00; drift 0.11 m

## F. Training-config audit (what the training actually ran)

- 29 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}}
- active library fixes: 1, decider terms: 1

## F2. Knobs this round trained with vs round 4 (2 differences)

- extra_dyn: [] -> [{"name": "agent_r05_base_still", "func": "dyn_base_still", "weight": 2.0, "params": {"phases": ["stand_after"], "std_v"
- prior.land: 1.0 -> 2.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r4: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7ecbae107d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r5: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7cd83081fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] library fixes: r4: []
  r5: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 2.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.1554, 0.2111]), rounds used 5, GPU 7.9 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.085 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.051 | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | 0.042 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.058 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.003 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 4.0 | <= 5 | pass |
| hold_posture_joints | eval.hold_pose_err_rad | 0.076 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.023 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.002 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 3.1 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 4.33 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.781 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.73 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.746 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 259.0 | >= 229.95000000000002 | pass |
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
