# Round 6 - quantitative report (step 1, before any diagnosis)

run `2026-10-26_06-16-00_cw2auto_r06`, best checkpoint `model_7000.pt` (score 5.72), evaluated: model_6500.pt 5.636, model_7000.pt 5.72, model_7495.pt 5.709

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 252.5 | 259.0 | -6.5 |
| robot_max_rotation_deg | 253.1 | 259.1 | -6 |
| robot_peak_pelvis_m | 0.77 | 0.782 | -0.012 |
| robot_airborne_s | 0.2 | 0.24 | -0.04 |
| landed_upright | True | True |  |
| end_tilt_deg | 12.2 | 16.8 | -4.6 |
| pelvis_rise_m | 0.043 | 0.049 | -0.006 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.635 | 0.63 | +0.005 |
| track_body_err_m | 0.0641 | 0.0583 | +0.0058 |
| track_joint_err | 0.8898 | 0.8706 | +0.0192 |
| post_fell | False | False |  |
| post_tilt_err_max_deg | 7.7 | 3.1 | +4.6 |
| post_drift_m | 0.0 | 0.002 | -0.002 |
| post_sway_m | 0.001 | 0.001 | +0 |
| post_pelvis_speed_max | 0.005 | 0.001 | +0.004 |
| post_action_change | 0.0002 | 0.0002 | +0 |
| post_feet_off_steps | 0 | 0 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | False |  |
| hold_tilt_err_max_deg | 9.4 | 4.0 | +5.4 |
| hold_height_err_m | 0.029 | 0.023 | +0.006 |
| hold_pose_err_rad | 0.081 | 0.076 | +0.005 |
| hold_pelvis_speed_max | 0.106 | 0.085 | +0.021 |
| hold_drift_m | 0.027 | 0.051 | -0.024 |
| hold_sway_m | 0.025 | 0.042 | -0.017 |
| hold_torso_angvel_rms | 0.077 | 0.058 | +0.019 |
| hold_action_change | 0.0034 | 0.0029 | +0.0005 |
| hold_feet_off_steps | 0 | 0 | +0 |
| early_fall | False | False |  |
| score | 5.72 | 5.767 | -0.047 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_06-16-00_cw2auto_r06/eval/_post_auto_model_7000.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.727 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-26_06-16-00_cw2auto_r06/eval/flip_auto_model_7000.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 1.0 | 0.0 | [256.4, 264.7, 273.0] | [10.5, 12.9, 16.5] |
| dr | 0.809 | 0.0 | [248.1, 258.9, 270.7] | [13.0, 17.1, 20.9] |
| delay1 | 0.652 | 0.016 | [242.4, 259.2, 273.8] | [15.0, 19.5, 25.0] |
| delay2 | 0.262 | 0.145 | [218.4, 250.8, 392.8] | [17.9, 23.9, 123.2] |
| kp085 | 0.73 | 0.004 | [247.6, 263.3, 278.0] | [13.4, 18.9, 22.9] |

## A3. Segment probe `7495` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [238, 238, 238] | 238 | stand | 0.906 |
| 16 | lunge | [222, 222, 222] | 238 | stand | 0.953 |
| 30 | lunge | [208, 208, 208] | 238 | stand | 0.922 |
| 46 | support | [192, 192, 192] | 238 | stand | 0.969 |
| 60 | support | [178, 178, 178] | 238 | stand | 0.938 |
| 81 | land | [20, 70, 157] | 151 | stand | 0.203 |
| 95 | settle | [143, 143, 143] | 238 | stand | 0.953 |
| 115 | stand | [123, 123, 123] | 238 | stand | 1.0 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 14 of 53 measurements beyond tolerance

- 3.3 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 65 vs reference 1 rad/s^2
- 3.3 asymmetry:wrist_roll - left/right differ 34 deg vs reference 1 deg
- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.26 m
- 1.8 joint:wrist_roll - left_wrist_roll_joint: mean |err| 27 deg (signed -27), step 5: robot -0.70 vs ref -0.02 rad
- 1.6 asymmetry:shoulder_pitch - left/right differ 18 deg vs reference 1 deg
- 1.5 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 23 deg (signed -23), step 8: robot -2.34 vs ref -1.84 rad

**lunge**: 9 of 51 measurements beyond tolerance

- 2.0 body:wrist_yaw - right_wrist_yaw_link: mean 0.16 m, max 0.28 m
- 1.7 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 30 vs reference 1 rad/s^2
- 1.3 joint:hip_yaw - right_hip_yaw_joint: mean |err| 20 deg (signed -20), step 38: robot -0.61 vs ref +0.03 rad
- 1.3 body:ankle_roll - left_ankle_roll_link: mean 0.10 m, max 0.17 m
- 1.3 body:elbow - left_elbow_link: mean 0.10 m, max 0.14 m
- 1.2 body:knee - left_knee_link: mean 0.09 m, max 0.12 m

**support**: 13 of 51 measurements beyond tolerance

- 2.5 asymmetry:hip_yaw - left/right differ 39 deg vs reference 14 deg
- 2.4 asymmetry:hip_pitch - left/right differ 92 deg vs reference 68 deg
- 2.1 body:ankle_roll - right_ankle_roll_link: mean 0.17 m, max 0.36 m
- 2.0 joint:wrist_roll - left_wrist_roll_joint: mean |err| 29 deg (signed +25), step 60: robot +1.24 vs ref +0.34 rad
- 1.6 body:wrist_yaw - left_wrist_yaw_link: mean 0.13 m, max 0.21 m
- 1.6 body:knee - right_knee_link: mean 0.13 m, max 0.19 m

**land**: 16 of 53 measurements beyond tolerance

- 3.0 contact:right_foot - right_foot off the floor for 9 of 14 steps the reference has it down
- 2.9 body:ankle_roll - left_ankle_roll_link: mean 0.23 m, max 0.36 m
- 2.7 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 47 vs reference 1 rad/s^2
- 2.6 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 38 deg (signed +38), step 84: robot +0.26 vs ref -0.80 rad
- 2.4 jitter:ankle_roll - left_ankle_roll_joint: joint acceleration RMS 38 vs reference 0 rad/s^2
- 2.3 body:knee - left_knee_link: mean 0.19 m, max 0.27 m

**settle**: 5 of 54 measurements beyond tolerance

- 2.0 body:ankle_roll - left_ankle_roll_link: mean 0.16 m, max 0.20 m
- 1.5 jitter:all - mean action change 0.077 (quiet < 0.05)
- 1.1 joint:ankle_pitch - right_ankle_pitch_joint: mean |err| 17 deg (signed +12), step 97: robot -0.15 vs ref -0.62 rad
- 1.1 asymmetry:hip_yaw - left/right differ 19 deg vs reference 8 deg
- 1.0 body:wrist_yaw - left_wrist_yaw_link: mean 0.08 m, max 0.15 m

**stand_after**: 2 of 54 measurements beyond tolerance

- 1.1 body:wrist_yaw - right_wrist_yaw_link: mean 0.08 m, max 0.12 m
- 1.0 joint:ankle_roll - left_ankle_roll_joint: mean |err| 15 deg (signed +15), step 141: robot +0.02 vs ref -0.26 rad

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.6 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.24 |
| 3.3 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.0579 |
| 1.0 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.402 |
| 1.3 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.362 |
| 2.0 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.209 |
| 1.2 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.387 |
| 1.1 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0.379 |
| 1.3 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.311 |
| 1.5 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.264 |
| 1.2 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.354 |
| 1.3 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.319 |
| 2.0 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.182 |
| 2.1 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.183 |
| 1.6 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.279 |
| 1.6 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.281 |
| 2.6 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.107 |
| 2.9 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.0997 |
| 2.1 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.179 |
| 2.3 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.157 |
| 1.1 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.369 |
| 3.0 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.1 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.376 |
| 1.1 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.383 |
| 1.5 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 0.431 |
| 1.0 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 0.445 |
| 2.0 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.204 |
| 1.6 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.245 |
| 1.6 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.254 |
| 2.4 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 3.3 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.7 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.309 |
| 1.7 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.407 |
| 1.5 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.268 |
| 1.1 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.421 |
| 2.0 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.198 |
| 2.5 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.2 | 0.111 |
| 1.4 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.4 | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | 0.126 |

41 of 101 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 0


## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.28| rad (end -0.15), reference max |0.51|
- arm joints mean |err| 3 deg; worst: left_elbow 6, left_shoulder_pitch 4, left_shoulder_yaw 4, right_elbow 3
- action change mean 0.017 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_ankle_pitch 4, left_ankle_pitch 4, right_shoulder_pitch 3, left_wrist_roll 3
- feet off the floor (> 6 cm): left 0, right 0 of 145 steps
- land (steps 81-94): pelvis speed mean 0.57 m/s, last 0.01; drift 0.09 m
- settle (steps 95-114): pelvis speed mean 0.18 m/s, last 0.17; drift 0.07 m
- stand_after (steps 115-239): pelvis speed mean 0.04 m/s, last 0.00; drift 0.06 m

## F. Training-config audit (what the training actually ran)

- 29 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['stand'], 'max_lift': 0.
- active library fixes: 1, decider terms: 1

## F2. Knobs this round trained with vs round 5 (5 differences)

- extra_dyn: [{"name": "agent_r05_base_still", "func": "dyn_base_still", "weight": 2.0, "params": {"phases": ["stand_after"], "std_v" -> [{"name": "agent_r05_base_still", "func": "dyn_base_still", "weight": 3.0, "params": {"phases": ["stand_after"], "std_v"
- prior.land: 2.0 -> 3.0
- terms.term_foot_lifted.max_lift: - -> 0.05
- terms.term_foot_lifted.phases: - -> ["stand"]
- terms.term_foot_lifted.planted_z: - -> 0.06

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r5: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7cd83081fd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r6: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7c91f067bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] flip terminations: r5: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}}
  r6: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None, 'term_below_reference': {'margin': 0.12, 'min_clear': 0.05}, 'term_foot_lifted': {'phases': ['st
- [train_dance] library fixes: r5: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 2.0)]
  r6: [('lib_cartwheel_2_contact_left_foot_stand', 1.0), ('agent_r05_base_still', 3.0)]

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [0.2111, -0.0995]), rounds used 6, GPU 9.5 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.106 | <= 0.15 | pass |
| hold_no_drift | eval.hold_drift_m | 0.027 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.025 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.077 | <= 0.2 | pass |
| hold_quiet | eval.hold_action_change | 0.003 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 9.4 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.081 | <= 0.15 | pass |
| hold_posture_height | eval.hold_height_err_m | 0.029 | <= 0.05 | pass |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | 0.0 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 7.7 | <= 10 | pass |
| critic_clean | critic.max_unwaived_severity | 3.67 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.809 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.652 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.73 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 252.5 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | True | == True | pass |

worst unwaived library check: cartwheel_2/contact:left_foot:land

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
