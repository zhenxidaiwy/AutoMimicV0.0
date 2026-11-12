# Round 3 - quantitative report (step 1, before any diagnosis)

run `2026-11-04_18-41-06_cw2wm_r03`, best checkpoint `model_1812.pt` (score 1.537), evaluated: model_527.pt 1.061, model_1172.pt 0.993, model_1812.pt 1.537

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 196.4 | 472.8 | -276 |
| robot_max_rotation_deg | 200.0 | 616.0 | -416 |
| robot_peak_pelvis_m | 0.778 | 8.456 | -7.68 |
| robot_airborne_s | 0.26 | 0.38 | -0.12 |
| landed_upright | False | False |  |
| end_tilt_deg | 90.0 | 0.0 | +90 |
| pelvis_rise_m | 0.016 | 5.615 | -5.6 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.786 | nan | +nan |
| track_body_err_m | 0.6319 | nan | +nan |
| track_joint_err | 3.1305 | nan | +nan |
| post_fell | True | False |  |
| post_tilt_err_max_deg | 70.2 | 19.9 | +50.3 |
| post_drift_m | 0.002 | nan | +nan |
| post_sway_m | 0.002 | nan | +nan |
| post_pelvis_speed_max | 0.002 | nan | +nan |
| post_action_change | 0.0001 | nan | +nan |
| post_feet_off_steps | 250 | 0 | +250 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | True | False |  |
| hold_tilt_err_max_deg | 70.7 | 19.9 | +50.8 |
| hold_height_err_m | 0.619 | nan | +nan |
| hold_pose_err_rad | 0.428 | nan | +nan |
| hold_pelvis_speed_max | 0.363 | nan | +nan |
| hold_drift_m | 0.051 | nan | +nan |
| hold_sway_m | 0.045 | nan | +nan |
| hold_torso_angvel_rms | 0.498 | nan | +nan |
| hold_action_change | 0.0066 | nan | +nan |
| hold_feet_off_steps | 100 | 0 | +100 |
| early_fall | False | False |  |
| score | 1.537 | nan | +nan |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_18-41-06_cw2wm_r03/eval/_post_auto_model_1812.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.751 | - |  |
| end_pelvis_m | 0.081 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_18-41-06_cw2wm_r03/eval/flip_auto_model_1812.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.0 | 0.0 | 1.0 | [101.6, 148.2, 229.9] | [78.1, 90.0, 95.0] | [0.001, 0.005, 0.057] |
| dr | 0.0 | 0.0 | 1.0 | [100.6, 147.0, 232.0] | [78.9, 90.3, 97.3] | [0.004, 0.019, 0.096] |
| delay1 | 0.0 | 0.0 | 1.0 | [101.4, 182.5, 241.3] | [79.7, 91.7, 98.0] | [0.006, 0.022, 0.205] |
| delay2 | 0.0 | 0.0 | 1.0 | [99.7, 180.0, 270.6] | [78.4, 90.5, 97.6] | [0.006, 0.044, 0.271] |
| kp085 | 0.0 | 0.0 | 1.0 | [98.4, 146.0, 235.0] | [79.2, 90.8, 98.8] | [0.005, 0.02, 0.124] |

## A3. Segment probe `1812` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [33, 42, 44] | 42 | lunge | 0.0 |
| 16 | lunge | [24, 25, 27] | 41 | lunge | 0.0 |
| 30 | lunge | [15, 16, 17] | 46 | support | 0.0 |
| 46 | support | [11, 12, 12] | 58 | support | 0.0 |
| 60 | support | [17, 19, 21] | 79 | support | 0.0 |
| 81 | land | [34, 53, 85] | 134 | stand | 0.016 |
| 95 | settle | [42, 57, 78] | 152 | stand | 0.0 |
| 115 | stand | [75, 120, 123] | 235 | stand | 0.484 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 20 of 53 measurements beyond tolerance

- 5.0 body:ankle_roll - left_ankle_roll_link: mean 0.40 m, max 0.62 m
- 3.7 contact:left_foot - left_foot off the floor for 11 of 16 steps the reference has it down
- 3.3 body:wrist_yaw - right_wrist_yaw_link: mean 0.26 m, max 0.42 m
- 2.6 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 45 vs reference 1 rad/s^2
- 2.3 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 35 deg (signed +35), step 11: robot -1.03 vs ref -1.85 rad
- 2.2 joint:knee - left_knee_joint: mean |err| 32 deg (signed +32), step 15: robot +0.77 vs ref +0.06 rad

**lunge**: 25 of 51 measurements beyond tolerance

- 6.1 body:ankle_roll - left_ankle_roll_link: mean 0.49 m, max 0.57 m
- 4.7 body:wrist_yaw - right_wrist_yaw_link: mean 0.37 m, max 0.57 m
- 4.1 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 62 deg (signed +62), step 45: robot +0.43 vs ref -1.70 rad
- 3.4 body:knee - left_knee_link: mean 0.28 m, max 0.40 m
- 3.3 body:elbow - right_elbow_link: mean 0.27 m, max 0.38 m
- 3.2 asymmetry:elbow - left/right differ 34 deg vs reference 3 deg

**support**: 30 of 51 measurements beyond tolerance

- 12.3 body:ankle_roll - right_ankle_roll_link: mean 0.98 m, max 1.48 m
- 9.3 body:knee - right_knee_link: mean 0.75 m, max 1.07 m
- 7.8 body:hip_roll - right_hip_roll_link: mean 0.62 m, max 0.78 m
- 7.6 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 115 deg (signed +115), step 52: robot +0.17 vs ref -2.21 rad
- 7.1 body:pelvis - pelvis: mean 0.56 m, max 0.66 m
- 7.0 body:torso - torso_link: mean 0.56 m, max 0.66 m

**land**: 32 of 53 measurements beyond tolerance

- 10.8 body:wrist_yaw - right_wrist_yaw_link: mean 0.86 m, max 1.18 m
- 9.5 body:ankle_roll - right_ankle_roll_link: mean 0.76 m, max 0.80 m
- 9.5 body:shoulder_roll - right_shoulder_roll_link: mean 0.76 m, max 0.92 m
- 8.9 body:elbow - right_elbow_link: mean 0.71 m, max 0.96 m
- 8.0 body:knee - right_knee_link: mean 0.64 m, max 0.70 m
- 7.1 body:torso - torso_link: mean 0.57 m, max 0.60 m

**settle**: 41 of 54 measurements beyond tolerance

- 15.7 body:wrist_yaw - right_wrist_yaw_link: mean 1.25 m, max 1.31 m
- 13.4 asymmetry:shoulder_pitch - left/right differ 146 deg vs reference 12 deg
- 13.0 body:elbow - right_elbow_link: mean 1.04 m, max 1.06 m
- 12.0 body:shoulder_roll - right_shoulder_roll_link: mean 0.96 m, max 0.99 m
- 11.8 body:ankle_roll - right_ankle_roll_link: mean 0.94 m, max 1.09 m
- 8.4 body:knee - right_knee_link: mean 0.67 m, max 0.75 m

**stand_after**: 32 of 54 measurements beyond tolerance

- 38.0 contact:left_foot - left_foot off the floor for 114 of 125 steps the reference has it down
- 17.7 body:wrist_yaw - left_wrist_yaw_link: mean 1.41 m, max 1.44 m
- 14.7 body:elbow - left_elbow_link: mean 1.17 m, max 1.18 m
- 12.0 body:shoulder_roll - left_shoulder_roll_link: mean 0.96 m, max 0.97 m
- 11.6 body:ankle_roll - left_ankle_roll_link: mean 0.93 m, max 1.02 m
- 9.5 asymmetry:elbow - left/right differ 99 deg vs reference 4 deg

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.5 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.272 |
| 1.5 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.268 |
| 1.8 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 0.215 |
| 1.1 | cartwheel_2/asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.393 |
| 3.7 | cartwheel_2/contact:left_foot:stand | dyn_contact | 1.0 | None | - |
| 1.1 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.389 |
| 2.9 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.0778 |
| 1.2 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.352 |
| 1.9 | cartwheel_2/joint:waist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.191 |
| 1.4 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.299 |
| 1.0 | cartwheel_2/joint:wrist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.404 |
| 6.1 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.0077 |
| 4.7 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.0242 |
| 3.4 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.0638 |
| 1.6 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.258 |
| 2.0 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.172 |
| 3.2 | cartwheel_2/asymmetry:elbow:lunge | dyn_sym | 0.0 | 0.2 | 0.0634 |
| 1.8 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.208 |
| 4.7 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.0163 |
| 4.3 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.0244 |
| 1.9 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.185 |
| 1.6 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.252 |
| 7.6 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 0.00127 |
| 2.9 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.077 |
| 3.3 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0575 |
| 1.5 | cartwheel_2/joint:waist_pitch:support | dyn_joint | 0.0 | 0.3 | 0.276 |
| 2.7 | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | 0.0939 |
| 2.7 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.0929 |
| 4.3 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0244 |
| 12.3 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 5.43e-05 |
| 4.5 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.0277 |
| 9.3 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.00058 |
| 1.8 | cartwheel_2/asymmetry:elbow:support | dyn_sym | 0.0 | 0.2 | 0.203 |
| 2.2 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.146 |
| 1.4 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.29 |
| 1.4 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.302 |
| 9.5 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.000489 |
| 10.8 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.000182 |
| 8.0 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.00161 |
| 1.9 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.183 |
| 3.2 | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.0589 |
| 1.0 | cartwheel_2/joint:knee:settle | dyn_joint | 0.0 | 0.3 | 0.416 |
| 7.5 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.00148 |
| 4.7 | cartwheel_2/asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | 0.0162 |
| 1.8 | cartwheel_2/asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.213 |
| 3.4 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.0503 |
| 3.0 | cartwheel_2/contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 1.7 | cartwheel_2/contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 4.7 | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 3.0 | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0746 |
| 5.0 | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0126 |
| 1.0 | cartwheel_2/asymmetry:ankle_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.411 |
| 3.2 | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0591 |
| 3.7 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0389 |
| 9.5 | cartwheel_2/asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.000245 |
| 4.9 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0137 |
| 38.0 | cartwheel_2/contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 17.7 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 7.22e-07 |
| 4.1 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.0273 |
| 15.7 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 3.62e-06 |
| 14.7 | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | 8.04e-06 |
| 11.8 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 8.26e-05 |
| 13.0 | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | 3.11e-05 |
| 12.0 | cartwheel_2/body:shoulder_roll:settle | dyn_body | 0.0 | 0.1 | 6.9e-05 |
| 12.0 | cartwheel_2/body:shoulder_roll:stand_after | dyn_body | 0.0 | 0.1 | 6.89e-05 |
| 6.4 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0036 |
| 11.6 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 9.19e-05 |
| 3.2 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.0636 |
| 2.9 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.6 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 1.8 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 4.1 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.0372 |
| 1.1 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.9 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.216 |
| 2.2 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.152 |
| 5.0 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.0182 |
| 3.3 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.0707 |
| 1.8 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 4.6 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.018 |
| 5.2 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.2 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.6 | 0.708 |
| 2.1 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.163 |
| 1.9 | cartwheel_2/jitter:wrist_roll:settle | dyn_quiet | 0.0 | 1.0 | - |
| 9.5 | cartwheel_2/body:shoulder_roll:land | dyn_body | 0.0 | 0.1 | 0.00049 |
| 8.9 | cartwheel_2/body:elbow:land | dyn_body | 0.0 | 0.1 | 0.000791 |
| 1.6 | cartwheel_2/joint:elbow:lunge | dyn_joint | 0.0 | 0.3 | 0.258 |
| 1.4 | cartwheel_2/joint:shoulder_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.291 |
| 1.2 | cartwheel_2/joint:wrist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.341 |
| 1.5 | cartwheel_2/joint:shoulder_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.281 |
| 1.0 | cartwheel_2/joint:waist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.412 |
| 13.4 | cartwheel_2/asymmetry:shoulder_pitch:settle | dyn_sym | 0.0 | 0.2 | 8.31e-06 |
| 8.4 | cartwheel_2/body:knee:settle | dyn_body | 0.0 | 0.1 | 0.00122 |
| 8.3 | cartwheel_2/body:torso:stand_after | dyn_body | 0.0 | 0.1 | 0.00135 |
| 7.8 | cartwheel_2/body:hip_roll:support | dyn_body | 0.0 | 0.1 | 0.00194 |
| 7.7 | cartwheel_2/body:pelvis:stand_after | dyn_body | 0.0 | 0.1 | 0.00207 |
| 7.3 | cartwheel_2/body:torso:settle | dyn_body | 0.0 | 0.1 | 0.00289 |
| 6.1 | cartwheel_2/body:knee:stand_after | dyn_body | 0.0 | 0.1 | 0.00765 |
| 1.9 | cartwheel_2/jitter:wrist_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 6.6 | cartwheel_2/body:hip_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.00504 |
| 7.1 | cartwheel_2/body:torso:land | dyn_body | 0.0 | 0.1 | 0.00345 |
| 6.6 | cartwheel_2/body:pelvis:land | dyn_body | 0.0 | 0.1 | 0.00504 |

101 of 131 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 33

- 7.1 joint:shoulder_pitch:settle - right_shoulder_pitch_joint: mean |err| 106 deg (signed +106), step 101: robot +0.32 vs ref -2.02 rad
- 7.1 body:pelvis:support - pelvis: mean 0.56 m, max 0.66 m
- 7.0 body:torso:support - torso_link: mean 0.56 m, max 0.66 m
- 6.7 body:pelvis:settle - pelvis: mean 0.54 m, max 0.58 m
- 6.6 body:hip_roll:land - right_hip_roll_link: mean 0.53 m, max 0.54 m
- 6.6 body:hip_roll:settle - right_hip_roll_link: mean 0.53 m, max 0.57 m
- 5.1 joint:ankle_pitch:stand_after - right_ankle_pitch_joint: mean |err| 76 deg (signed -76), step 135: robot -0.88 vs ref +0.48 rad
- 4.9 body:shoulder_roll:support - left_shoulder_roll_link: mean 0.39 m, max 0.63 m
- 4.7 joint:elbow:stand_after - right_elbow_joint: mean |err| 70 deg (signed -70), step 165: robot -0.30 vs ref +1.01 rad
- 4.5 asymmetry:shoulder_pitch:stand_after - left/right differ 59 deg vs reference 15 deg
- 4.2 joint:waist_yaw:land - waist_yaw_joint: mean |err| 64 deg (signed -64), step 87: robot -1.65 vs ref -0.41 rad
- 4.0 asymmetry:shoulder_pitch:land - left/right differ 58 deg vs reference 18 deg
- 4.0 asymmetry:shoulder_pitch:support - left/right differ 58 deg vs reference 17 deg
- 3.7 joint:shoulder_roll:land - left_shoulder_roll_joint: mean |err| 55 deg (signed +55), step 81: robot +1.32 vs ref +0.07 rad
- 3.6 joint:shoulder_pitch:stand_after - left_shoulder_pitch_joint: mean |err| 54 deg (signed -54), step 115: robot -3.10 vs ref -1.86 rad

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |1.23| rad (end +0.16), reference max |0.51|
- arm joints mean |err| 35 deg; worst: right_elbow 62, left_shoulder_pitch 54, left_shoulder_roll 42, left_shoulder_yaw 33
- action change mean 0.052 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_elbow 21, right_shoulder_roll 17, right_shoulder_pitch 17, left_shoulder_yaw 17
- feet off the floor (> 6 cm): left 131, right 5 of 145 steps
- land (steps 81-94): pelvis speed mean 0.51 m/s, last 0.39; drift 0.13 m
- settle (steps 95-114): pelvis speed mean 0.32 m/s, last 0.33; drift 0.03 m
- stand_after (steps 115-239): pelvis speed mean 0.08 m/s, last 0.00; drift 0.19 m

## F. Training-config audit (what the training actually ran)

- 30 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 3, decider terms: 0

## F2. Knobs this round trained with vs round 2 (0 differences)


Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r2: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7bf4591d4d60>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r3: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x780bb02813a0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [nan, nan]), rounds used 3, GPU 3.0 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | True | == False | FAIL |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.363 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.051 | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | 0.045 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.498 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.007 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 70.7 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.428 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.619 | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 100 | <= 0 | FAIL |
| post_no_fall | eval.post_fell | True | == False | FAIL |
| post_no_drift | eval.post_drift_m | 0.002 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 70.2 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 38.0 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 196.4 | >= 229.95000000000002 | FAIL |
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
