# Round 2 - quantitative report (step 1, before any diagnosis)

run `2026-10-25_23-01-01_cw2auto_r02`, best checkpoint `model_1000.pt` (score 1.82), evaluated: model_500.pt 1.033, model_1000.pt 1.82, model_1499.pt 1.573

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 232.5 | 231.0 | +1.5 |
| robot_max_rotation_deg | 234.1 | 236.0 | -1.9 |
| robot_peak_pelvis_m | 0.696 | 0.747 | -0.051 |
| robot_airborne_s | 0.08 | 0.12 | -0.04 |
| landed_upright | False | False |  |
| end_tilt_deg | 76.8 | 102.7 | -25.9 |
| pelvis_rise_m | 0.063 | 0.007 | +0.056 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.169 | 0.467 | -0.298 |
| track_body_err_m | 0.6927 | 0.6794 | +0.0133 |
| track_joint_err | 3.8967 | 4.5906 | -0.694 |
| post_fell | True | True |  |
| post_tilt_err_max_deg | 73.4 | 87.6 | -14.2 |
| post_drift_m | 0.25 | 0.695 | -0.445 |
| post_sway_m | 0.211 | 0.556 | -0.345 |
| post_pelvis_speed_max | 0.726 | 1.543 | -0.817 |
| post_action_change | 0.1243 | 0.8809 | -0.757 |
| post_feet_off_steps | 250 | 250 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | True | True |  |
| hold_tilt_err_max_deg | 77.4 | 80.3 | -2.9 |
| hold_height_err_m | 0.57 | 0.641 | -0.071 |
| hold_pose_err_rad | 0.353 | 0.527 | -0.174 |
| hold_pelvis_speed_max | 1.112 | 0.494 | +0.618 |
| hold_drift_m | 0.499 | 0.036 | +0.463 |
| hold_sway_m | 0.264 | 0.045 | +0.219 |
| hold_torso_angvel_rms | 3.123 | 2.101 | +1.02 |
| hold_action_change | 0.5776 | 0.3322 | +0.245 |
| hold_feet_off_steps | 199 | 200 | -1 |
| early_fall | False | False |  |
| score | 1.82 | 1.93 | -0.11 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-25_23-01-01_cw2auto_r02/eval/_post_auto_model_1000.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.751 | - |  |
| end_pelvis_m | 0.083 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-25_23-01-01_cw2auto_r02/eval/flip_auto_model_1000.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m)

| scenario | success | fell | rotation p5/50/95 | end tilt p5/50/95 |
|---|---|---|---|---|
| nominal | 0.0 | 1.0 | [61.8, 167.4, 242.8] | [73.7, 96.6, 111.5] |
| dr | 0.0 | 1.0 | [68.4, 182.8, 241.7] | [75.0, 97.0, 114.0] |
| delay1 | 0.0 | 1.0 | [102.9, 202.3, 292.3] | [75.9, 99.4, 118.3] |
| delay2 | 0.0 | 1.0 | [97.0, 216.8, 366.8] | [76.8, 99.1, 120.2] |
| kp085 | 0.0 | 1.0 | [71.8, 182.1, 241.3] | [78.4, 96.5, 114.5] |

## A3. Segment probe `1499` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [13, 24, 28] | 24 | lunge | 0.0 |
| 16 | lunge | [20, 21, 22] | 37 | lunge | 0.0 |
| 30 | lunge | [8, 9, 9] | 39 | lunge | 0.0 |
| 46 | support | [4, 5, 5] | 51 | support | 0.0 |
| 60 | support | [71, 178, 178] | 238 | stand | 0.75 |
| 81 | land | [15, 18, 157] | 99 | settle | 0.156 |
| 95 | settle | [143, 143, 143] | 238 | stand | 0.938 |
| 115 | stand | [123, 123, 123] | 238 | stand | 0.984 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 27 of 53 measurements beyond tolerance

- 6.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 99 deg (signed +99), step 15: robot +1.99 vs ref -1.81 rad
- 6.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.50 m, max 0.84 m
- 5.0 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 97 vs reference 1 rad/s^2
- 4.3 jitter:ankle_pitch - right_ankle_pitch_joint: joint acceleration RMS 130 vs reference 5 rad/s^2
- 3.8 body:elbow - left_elbow_link: mean 0.31 m, max 0.50 m
- 3.5 asymmetry:shoulder_pitch - left/right differ 37 deg vs reference 1 deg

**lunge**: 34 of 51 measurements beyond tolerance

- 16.0 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 239 deg (signed +239), step 23: robot +2.68 vs ref -1.78 rad
- 11.3 asymmetry:shoulder_pitch - left/right differ 125 deg vs reference 11 deg
- 9.4 body:wrist_yaw - left_wrist_yaw_link: mean 0.75 m, max 1.12 m
- 8.4 body:elbow - left_elbow_link: mean 0.67 m, max 0.89 m
- 7.6 body:shoulder_roll - left_shoulder_roll_link: mean 0.61 m, max 0.74 m
- 6.7 asymmetry:elbow - left/right differ 70 deg vs reference 3 deg

**support**: 30 of 51 measurements beyond tolerance

- 13.7 body:ankle_roll - left_ankle_roll_link: mean 1.10 m, max 1.48 m
- 13.3 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 200 deg (signed +200), step 55: robot +2.68 vs ref -2.00 rad
- 9.3 body:knee - left_knee_link: mean 0.74 m, max 1.01 m
- 8.3 body:hip_roll - left_hip_roll_link: mean 0.67 m, max 0.76 m
- 6.6 body:pelvis - pelvis: mean 0.53 m, max 0.64 m
- 6.4 body:torso - torso_link: mean 0.51 m, max 0.65 m

**land**: 41 of 53 measurements beyond tolerance

- 11.8 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 177 deg (signed +177), step 94: robot +2.16 vs ref -1.84 rad
- 10.1 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 172 vs reference 1 rad/s^2
- 9.5 body:shoulder_roll - left_shoulder_roll_link: mean 0.76 m, max 0.95 m
- 9.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.74 m, max 0.99 m
- 8.7 body:ankle_roll - right_ankle_roll_link: mean 0.69 m, max 0.78 m
- 8.0 body:knee - right_knee_link: mean 0.64 m, max 0.71 m

**settle**: 41 of 54 measurements beyond tolerance

- 16.9 body:wrist_yaw - left_wrist_yaw_link: mean 1.36 m, max 1.41 m
- 13.7 body:elbow - left_elbow_link: mean 1.10 m, max 1.13 m
- 12.1 body:shoulder_roll - left_shoulder_roll_link: mean 0.97 m, max 1.00 m
- 10.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 159 deg (signed +159), step 95: robot +2.16 vs ref -1.82 rad
- 9.4 body:ankle_roll - left_ankle_roll_link: mean 0.75 m, max 0.98 m
- 8.1 body:knee - left_knee_link: mean 0.65 m, max 0.71 m

**stand_after**: 44 of 54 measurements beyond tolerance

- 41.7 contact:right_foot - right_foot off the floor for 125 of 125 steps
- 41.3 contact:left_foot - left_foot off the floor for 124 of 125 steps
- 21.8 jitter:knee - right_knee_joint: joint acceleration RMS 327 vs reference 0 rad/s^2
- 17.4 body:wrist_yaw - right_wrist_yaw_link: mean 1.40 m, max 1.49 m
- 15.4 body:elbow - right_elbow_link: mean 1.23 m, max 1.27 m
- 12.2 jitter:hip_yaw - right_hip_yaw_joint: joint acceleration RMS 284 vs reference 3 rad/s^2

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.0 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.172 |
| 3.1 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.0649 |
| 3.5 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.0461 |
| 1.4 | cartwheel_2/asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.303 |
| 1.4 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.285 |
| 2.7 | cartwheel_2/contact:left_foot:stand | dyn_contact | 0.0 | None | - |
| 2.0 | cartwheel_2/contact:right_foot:stand | dyn_contact | 0.0 | None | - |
| 1.8 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.215 |
| 2.6 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.0994 |
| 3.9 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.0342 |
| 1.1 | cartwheel_2/joint:waist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.376 |
| 1.8 | cartwheel_2/joint:waist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.215 |
| 1.6 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.237 |
| 1.2 | cartwheel_2/joint:wrist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.363 |
| 6.6 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.00519 |
| 9.4 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.000564 |
| 5.1 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.0166 |
| 3.7 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.0413 |
| 6.7 | cartwheel_2/asymmetry:elbow:lunge | dyn_sym | 0.0 | 0.2 | 0.00282 |
| 2.1 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.155 |
| 4.1 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.0281 |
| 4.7 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.0171 |
| 1.7 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.226 |
| 1.5 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.266 |
| 13.3 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 9.03e-06 |
| 2.3 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.13 |
| 1.7 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.23 |
| 1.1 | cartwheel_2/joint:waist_pitch:support | dyn_joint | 0.0 | 0.3 | 0.388 |
| 3.1 | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | 0.0651 |
| 3.6 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.0424 |
| 4.5 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.019 |
| 13.7 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 1.71e-05 |
| 6.0 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.00848 |
| 9.3 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.000584 |
| 4.1 | cartwheel_2/asymmetry:elbow:support | dyn_sym | 0.0 | 0.2 | 0.0275 |
| 4.0 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0308 |
| 1.9 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.184 |
| 1.1 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.374 |
| 8.7 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.000961 |
| 9.3 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.000585 |
| 8.0 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.00162 |
| 4.7 | cartwheel_2/asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.016 |
| 4.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 2.2 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.149 |
| 2.0 | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.176 |
| 1.3 | cartwheel_2/joint:knee:settle | dyn_joint | 0.0 | 0.3 | 0.317 |
| 2.7 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.0908 |
| 1.1 | cartwheel_2/asymmetry:ankle_pitch:settle | dyn_sym | 0.0 | 0.2 | 0.383 |
| 1.4 | cartwheel_2/asymmetry:ankle_roll:settle | dyn_sym | 0.0 | 0.2 | 0.297 |
| 2.2 | cartwheel_2/asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | 0.144 |
| 7.3 | cartwheel_2/asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.00179 |
| 7.0 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.00226 |
| 6.7 | cartwheel_2/contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 6.7 | cartwheel_2/contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 5.6 | cartwheel_2/jitter:all:settle | dyn_quiet | 0.0 | 1.0 | - |
| 3.5 | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0456 |
| 2.3 | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.131 |
| 1.8 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.209 |
| 3.1 | cartwheel_2/asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.0688 |
| 3.2 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0618 |
| 41.3 | cartwheel_2/contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 41.7 | cartwheel_2/contact:right_foot:stand_after | dyn_contact | 0.0 | None | - |
| 11.3 | cartwheel_2/jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 17.4 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 8.71e-07 |
| 16.0 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 8.94e-07 |
| 16.9 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 1.29e-06 |
| 15.4 | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | 4.57e-06 |
| 9.4 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.000544 |
| 13.7 | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | 1.72e-05 |
| 21.8 | cartwheel_2/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.2 | cartwheel_2/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.1 | cartwheel_2/body:shoulder_roll:settle | dyn_body | 0.0 | 0.1 | 6.17e-05 |
| 12.0 | cartwheel_2/body:shoulder_roll:stand_after | dyn_body | 0.0 | 0.1 | 6.52e-05 |
| 11.8 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 3.37e-05 |
| 11.6 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 9.48e-05 |

75 of 86 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 89

- 11.3 asymmetry:shoulder_pitch:lunge - left/right differ 125 deg vs reference 11 deg
- 10.6 joint:shoulder_pitch:settle - left_shoulder_pitch_joint: mean |err| 159 deg (signed +159), step 95: robot +2.16 vs ref -1.82 rad
- 10.1 jitter:wrist_roll:land - left_wrist_roll_joint: joint acceleration RMS 172 vs reference 1 rad/s^2
- 9.8 jitter:ankle_roll:stand_after - right_ankle_roll_joint: joint acceleration RMS 214 vs reference 2 rad/s^2
- 9.5 body:shoulder_roll:land - left_shoulder_roll_link: mean 0.76 m, max 0.95 m
- 9.1 jitter:ankle_pitch:stand_after - right_ankle_pitch_joint: joint acceleration RMS 188 vs reference 2 rad/s^2
- 8.4 body:elbow:lunge - left_elbow_link: mean 0.67 m, max 0.89 m
- 8.3 body:hip_roll:support - left_hip_roll_link: mean 0.67 m, max 0.76 m
- 8.1 body:knee:settle - left_knee_link: mean 0.65 m, max 0.71 m
- 8.0 body:knee:stand_after - left_knee_link: mean 0.64 m, max 0.73 m
- 7.8 body:elbow:land - left_elbow_link: mean 0.63 m, max 0.92 m
- 7.8 body:torso:settle - torso_link: mean 0.62 m, max 0.64 m
- 7.6 body:torso:stand_after - torso_link: mean 0.61 m, max 0.65 m
- 7.6 body:shoulder_roll:lunge - left_shoulder_roll_link: mean 0.61 m, max 0.74 m
- 7.2 body:pelvis:settle - pelvis: mean 0.58 m, max 0.60 m

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.53| rad (end -0.05), reference max |0.51|
- arm joints mean |err| 29 deg; worst: left_shoulder_pitch 65, right_elbow 49, right_shoulder_pitch 37, right_shoulder_roll 31
- action change mean 0.527 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_knee 264, right_knee 251, right_hip_yaw 201, left_hip_pitch 140
- feet off the floor (> 6 cm): left 144, right 145 of 145 steps
- land (steps 81-94): pelvis speed mean 0.36 m/s, last 0.39; drift 0.03 m
- settle (steps 95-114): pelvis speed mean 0.25 m/s, last 0.16; drift 0.05 m
- stand_after (steps 115-239): pelvis speed mean 0.42 m/s, last 0.24; drift 0.64 m

## F. Training-config audit (what the training actually ran)

- 27 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 0, decider terms: 0

## F2. Knobs this round trained with vs round 1 (10 differences)

- reference.labels: - -> "labels_hold_50fps.npz"
- reference.variant: - -> "plant_vlm_hold"
- terms.term_flight_spread: - -> null
- terms.term_flight_spread.max_d: 0.6 -> -
- terms.term_leg_twist: - -> null
- terms.term_leg_twist.max_knee_sep: 0.45 -> -
- terms.term_leg_twist.max_roll: 0.6 -> -
- terms.term_leg_twist.max_yaw: 0.8 -> -
- weights.flip_land_balance: 2.0 -> 0.0
- weights.flip_leg_sym: 1.0 -> 0.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r1: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x709136e1bd80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r2: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7792b6ec3d80>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] flip rewards x2.0: r1: {'flip_pushoff': 4.0, 'flip_lean': 2.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 2.0, 'flip_plane_axis': 3.0, 'flip_plane_rate': 2.0, 'flip_leg_sym': 2.0, 'flip_leg_track': 2.0, 'flip_leg_calm': 1.0, 'flip_feet_together': 4.0, '
  r2: {'flip_pushoff': 4.0, 'flip_lean': 2.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 2.0, 'flip_plane_axis': 3.0, 'flip_plane_rate': 2.0, 'flip_leg_sym': 0.0, 'flip_leg_track': 2.0, 'flip_leg_calm': 1.0, 'flip_feet_together': 4.0, '
- [train_dance] flip terminations: r1: {'term_flight_spread': {'max_d': 0.6}, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': {'max_roll': 0.6, 'max_yaw': 0.8, 'max_knee_sep': 0.45}}
  r2: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds []), rounds used 2, GPU 3.2 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | True | == False | FAIL |
| hold_still_speed | eval.hold_pelvis_speed_max | 1.112 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.499 | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | 0.264 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 3.123 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.578 | <= 0.1 | FAIL |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 77.4 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.353 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.57 | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 199 | <= 0 | FAIL |
| post_no_fall | eval.post_fell | True | == False | FAIL |
| post_no_drift | eval.post_drift_m | 0.25 | <= 0.15 | FAIL |
| post_posture | eval.post_tilt_err_max_deg | 73.4 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 41.67 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 232.5 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | False | == True | FAIL |

worst unwaived library check: cartwheel_2/contact:right_foot:stand_after

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
