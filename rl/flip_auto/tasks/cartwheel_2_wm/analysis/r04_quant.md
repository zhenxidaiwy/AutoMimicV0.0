# Round 4 - quantitative report (step 1, before any diagnosis)

run `2026-11-04_19-49-26_cw2wm_r04`, best checkpoint `model_2294.pt` (score 1.112), evaluated: model_2294.pt 1.112, model_2940.pt 0.763

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 142.0 | 196.4 | -54.4 |
| robot_max_rotation_deg | 144.4 | 200.0 | -55.6 |
| robot_peak_pelvis_m | 0.769 | 0.778 | -0.009 |
| robot_airborne_s | 0.24 | 0.26 | -0.02 |
| landed_upright | False | False |  |
| end_tilt_deg | 92.2 | 90.0 | +2.2 |
| pelvis_rise_m | 0.004 | 0.016 | -0.012 |
| stand_stable | False | False |  |
| stand_feet_d_end | 0.218 | 0.786 | -0.568 |
| track_body_err_m | 0.6218 | 0.6319 | -0.0101 |
| track_joint_err | 3.369 | 3.1305 | +0.239 |
| post_fell | True | True |  |
| post_tilt_err_max_deg | 72.3 | 70.2 | +2.1 |
| post_drift_m | 0.005 | 0.002 | +0.003 |
| post_sway_m | 0.003 | 0.002 | +0.001 |
| post_pelvis_speed_max | 0.002 | 0.002 | +0 |
| post_action_change | 0.0003 | 0.0001 | +0.0002 |
| post_feet_off_steps | 250 | 250 | +0 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | True | True |  |
| hold_tilt_err_max_deg | 73.1 | 70.7 | +2.4 |
| hold_height_err_m | 0.537 | 0.619 | -0.082 |
| hold_pose_err_rad | 0.496 | 0.428 | +0.068 |
| hold_pelvis_speed_max | 0.189 | 0.363 | -0.174 |
| hold_drift_m | 0.02 | 0.051 | -0.031 |
| hold_sway_m | 0.021 | 0.045 | -0.024 |
| hold_torso_angvel_rms | 0.471 | 0.498 | -0.027 |
| hold_action_change | 0.0178 | 0.0066 | +0.0112 |
| hold_feet_off_steps | 200 | 100 | +100 |
| early_fall | False | False |  |
| score | 1.112 | 1.537 | -0.425 |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_19-49-26_cw2wm_r04/eval/_post_auto_model_2294.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.758 | - |  |
| end_pelvis_m | 0.163 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_19-49-26_cw2wm_r04/eval/flip_auto_model_2294.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.0 | 0.0 | 1.0 | [106.1, 144.9, 227.3] | [78.6, 91.8, 107.2] | [0.0, 0.01, 0.341] |
| dr | 0.0 | 0.0 | 1.0 | [106.5, 159.5, 247.0] | [79.0, 95.2, 110.9] | [0.005, 0.028, 0.376] |
| delay1 | 0.0 | 0.0 | 1.0 | [104.1, 149.9, 285.5] | [81.5, 92.2, 111.4] | [0.006, 0.038, 0.254] |
| delay2 | 0.0 | 0.0 | 1.0 | [102.9, 161.7, 392.1] | [81.3, 94.5, 113.9] | [0.009, 0.081, 0.434] |
| kp085 | 0.0 | 0.0 | 1.0 | [87.2, 122.0, 183.5] | [81.5, 94.5, 99.7] | [0.006, 0.026, 0.163] |

## A3. Segment probe `2940` (start at frame s with the training randomisation, lost = anchor height error > 0.4 m or torso orientation error > 1 rad)

| start | phase | lost after steps p10/50/90 | lost at frame (median) | phase lost | never lost |
|---|---|---|---|---|---|
| 0 | stand | [43, 48, 58] | 48 | support | 0.0 |
| 16 | lunge | [38, 41, 45] | 57 | support | 0.0 |
| 30 | lunge | [23, 25, 26] | 55 | support | 0.0 |
| 46 | support | [11, 12, 14] | 58 | support | 0.0 |
| 60 | support | [16, 17, 25] | 77 | support | 0.0 |
| 81 | land | [36, 50, 64] | 131 | stand | 0.0 |
| 95 | settle | [64, 87, 132] | 182 | stand | 0.094 |
| 115 | stand | [114, 123, 123] | 238 | stand | 0.828 |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 16 of 53 measurements beyond tolerance

- 4.0 contact:left_foot - left_foot off the floor for 12 of 16 steps the reference has it down
- 2.8 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 42 deg (signed +42), step 12: robot -0.81 vs ref -1.85 rad
- 2.5 body:wrist_yaw - right_wrist_yaw_link: mean 0.20 m, max 0.29 m
- 2.5 joint:elbow - right_elbow_joint: mean |err| 37 deg (signed -37), step 14: robot -0.35 vs ref +0.61 rad
- 2.2 joint:knee - left_knee_joint: mean |err| 34 deg (signed +34), step 15: robot +0.81 vs ref +0.06 rad
- 2.2 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 38 vs reference 1 rad/s^2

**lunge**: 15 of 51 measurements beyond tolerance

- 3.6 body:wrist_yaw - left_wrist_yaw_link: mean 0.29 m, max 0.35 m
- 3.6 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 55 deg (signed +55), step 45: robot -0.20 vs ref -1.63 rad
- 3.2 body:ankle_roll - left_ankle_roll_link: mean 0.26 m, max 0.34 m
- 2.4 body:elbow - left_elbow_link: mean 0.20 m, max 0.23 m
- 2.4 asymmetry:shoulder_yaw - left/right differ 34 deg vs reference 10 deg
- 2.3 joint:elbow - right_elbow_joint: mean |err| 34 deg (signed -34), step 23: robot -0.37 vs ref +0.63 rad

**support**: 23 of 51 measurements beyond tolerance

- 10.7 body:ankle_roll - left_ankle_roll_link: mean 0.86 m, max 1.25 m
- 9.1 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 137 deg (signed +137), step 57: robot +1.16 vs ref -2.15 rad
- 8.0 body:knee - left_knee_link: mean 0.64 m, max 0.95 m
- 7.2 body:hip_roll - left_hip_roll_link: mean 0.57 m, max 0.76 m
- 6.3 body:pelvis - pelvis: mean 0.50 m, max 0.63 m
- 6.1 body:torso - torso_link: mean 0.49 m, max 0.63 m

**land**: 37 of 53 measurements beyond tolerance

- 11.0 body:wrist_yaw - left_wrist_yaw_link: mean 0.88 m, max 1.27 m
- 10.1 body:shoulder_roll - left_shoulder_roll_link: mean 0.81 m, max 0.93 m
- 10.1 body:elbow - left_elbow_link: mean 0.81 m, max 1.09 m
- 9.5 body:ankle_roll - right_ankle_roll_link: mean 0.76 m, max 0.92 m
- 8.4 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 143 vs reference 1 rad/s^2
- 7.9 body:knee - right_knee_link: mean 0.64 m, max 0.78 m

**settle**: 43 of 54 measurements beyond tolerance

- 16.7 body:wrist_yaw - left_wrist_yaw_link: mean 1.34 m, max 1.47 m
- 13.8 body:elbow - left_elbow_link: mean 1.11 m, max 1.19 m
- 11.1 body:shoulder_roll - left_shoulder_roll_link: mean 0.89 m, max 0.92 m
- 10.2 body:ankle_roll - left_ankle_roll_link: mean 0.82 m, max 1.15 m
- 9.6 asymmetry:shoulder_yaw - left/right differ 110 deg vs reference 15 deg
- 7.9 asymmetry:shoulder_pitch - left/right differ 91 deg vs reference 12 deg

**stand_after**: 40 of 54 measurements beyond tolerance

- 41.7 contact:left_foot - left_foot off the floor for 125 of 125 steps the reference has it down
- 41.7 contact:right_foot - right_foot off the floor for 125 of 125 steps the reference has it down
- 17.2 body:wrist_yaw - right_wrist_yaw_link: mean 1.38 m, max 1.39 m
- 14.7 asymmetry:shoulder_yaw - left/right differ 151 deg vs reference 5 deg
- 14.4 body:elbow - left_elbow_link: mean 1.15 m, max 1.17 m
- 12.0 body:shoulder_roll - left_shoulder_roll_link: mean 0.96 m, max 0.97 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 2.5 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.115 |
| 4.0 | cartwheel_2/contact:left_foot:stand | dyn_contact | 1.0 | None | - |
| 1.2 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.346 |
| 2.1 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.155 |
| 1.5 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.265 |
| 3.2 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.0755 |
| 3.6 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.0542 |
| 1.8 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.229 |
| 2.4 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.123 |
| 1.8 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.216 |
| 3.1 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.0657 |
| 3.5 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.0462 |
| 1.6 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.255 |
| 2.0 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.17 |
| 9.1 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 0.000349 |
| 2.3 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.139 |
| 3.5 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.046 |
| 2.6 | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | 0.107 |
| 1.7 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.229 |
| 3.5 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0465 |
| 10.7 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 0.000191 |
| 4.5 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.0274 |
| 8.0 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.00162 |
| 2.5 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.112 |
| 2.3 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.129 |
| 9.5 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.000502 |
| 11.0 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.000152 |
| 7.9 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.00174 |
| 2.8 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.0859 |
| 4.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.5 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.282 |
| 2.3 | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.137 |
| 2.1 | cartwheel_2/joint:knee:settle | dyn_joint | 0.0 | 0.3 | 0.155 |
| 7.4 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.00163 |
| 6.1 | cartwheel_2/asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | 0.00471 |
| 1.6 | cartwheel_2/asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | 0.247 |
| 1.7 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.222 |
| 3.7 | cartwheel_2/contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 6.7 | cartwheel_2/contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 6.1 | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 5.1 | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0114 |
| 4.6 | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0176 |
| 14.7 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 2.8e-06 |
| 7.1 | cartwheel_2/asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | 0.00201 |
| 1.1 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.394 |
| 41.7 | cartwheel_2/contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 41.7 | cartwheel_2/contact:right_foot:stand_after | dyn_contact | 0.0 | None | - |
| 17.2 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 1.05e-06 |
| 3.6 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.0418 |
| 16.7 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 1.54e-06 |
| 14.4 | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | 9.85e-06 |
| 10.2 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.000288 |
| 13.8 | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | 1.57e-05 |
| 2.3 | cartwheel_2/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.6 | cartwheel_2/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 11.1 | cartwheel_2/body:shoulder_roll:settle | dyn_body | 0.0 | 0.1 | 0.000136 |
| 12.0 | cartwheel_2/body:shoulder_roll:stand_after | dyn_body | 0.0 | 0.1 | 6.82e-05 |
| 5.0 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0123 |
| 10.2 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.000289 |
| 1.8 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.207 |
| 5.0 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 2.2 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 8.4 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 3.9 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.0431 |
| 1.7 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 4.4 | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | 0.0219 |
| 1.1 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.423 |
| 2.2 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.141 |
| 2.2 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.178 |
| 2.5 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.138 |
| 1.5 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 5.4 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.00881 |
| 5.1 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 1.5 | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | 0.282 |
| 2.2 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.153 |
| 3.4 | cartwheel_2/jitter:wrist_roll:settle | dyn_quiet | 0.0 | 1.0 | - |
| 1.1 | cartwheel_2/jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 1.8 | cartwheel_2/jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 10.1 | cartwheel_2/body:shoulder_roll:land | dyn_body | 0.0 | 0.1 | 0.0003 |
| 10.1 | cartwheel_2/body:elbow:land | dyn_body | 0.0 | 0.1 | 0.000314 |
| 2.3 | cartwheel_2/joint:elbow:lunge | dyn_joint | 0.0 | 0.3 | 0.135 |
| 1.1 | cartwheel_2/joint:shoulder_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0.384 |
| 1.3 | cartwheel_2/joint:shoulder_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.328 |
| 7.9 | cartwheel_2/asymmetry:shoulder_pitch:settle | dyn_sym | 0.0 | 0.2 | 0.00105 |
| 6.7 | cartwheel_2/body:knee:settle | dyn_body | 0.0 | 0.1 | 0.00479 |
| 7.2 | cartwheel_2/body:torso:stand_after | dyn_body | 0.0 | 0.1 | 0.00328 |
| 7.2 | cartwheel_2/body:hip_roll:support | dyn_body | 0.0 | 0.1 | 0.00327 |
| 6.8 | cartwheel_2/body:pelvis:stand_after | dyn_body | 0.0 | 0.1 | 0.00431 |
| 6.2 | cartwheel_2/body:torso:settle | dyn_body | 0.0 | 0.1 | 0.00706 |
| 9.6 | cartwheel_2/asymmetry:shoulder_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.000234 |
| 7.7 | cartwheel_2/body:knee:stand_after | dyn_body | 0.0 | 0.1 | 0.00207 |
| 7.2 | cartwheel_2/jitter:wrist_yaw:settle | dyn_quiet | 0.0 | 1.0 | - |
| 6.8 | cartwheel_2/body:hip_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.00449 |
| 6.7 | cartwheel_2/body:torso:land | dyn_body | 0.0 | 0.1 | 0.00474 |
| 6.3 | cartwheel_2/body:pelvis:land | dyn_body | 0.0 | 0.1 | 0.00624 |

95 of 131 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 40

- 6.3 body:pelvis:support - pelvis: mean 0.50 m, max 0.63 m
- 6.2 joint:shoulder_yaw:stand_after - right_shoulder_yaw_joint: mean |err| 93 deg (signed +93), step 126: robot +1.68 vs ref -0.63 rad
- 6.1 body:torso:support - torso_link: mean 0.49 m, max 0.63 m
- 6.0 joint:shoulder_pitch:settle - right_shoulder_pitch_joint: mean |err| 90 deg (signed +90), step 110: robot +0.24 vs ref -2.07 rad
- 6.0 body:hip_roll:land - right_hip_roll_link: mean 0.48 m, max 0.51 m
- 5.6 body:pelvis:settle - pelvis: mean 0.45 m, max 0.58 m
- 5.4 joint:wrist_yaw:stand_after - right_wrist_yaw_joint: mean |err| 82 deg (signed +82), step 215: robot +1.56 vs ref -0.05 rad
- 5.0 body:hip_roll:settle - right_hip_roll_link: mean 0.40 m, max 0.54 m
- 4.9 joint:shoulder_yaw:settle - left_shoulder_yaw_joint: mean |err| 73 deg (signed +73), step 112: robot +1.97 vs ref +0.42 rad
- 4.8 body:shoulder_roll:support - left_shoulder_roll_link: mean 0.38 m, max 0.69 m
- 4.4 joint:shoulder_roll:land - left_shoulder_roll_joint: mean |err| 66 deg (signed +66), step 81: robot +1.41 vs ref +0.07 rad
- 4.3 jitter:wrist_yaw:stand_after - left_wrist_yaw_joint: joint acceleration RMS 67 vs reference 0 rad/s^2
- 4.1 jitter:wrist_pitch:land - left_wrist_pitch_joint: joint acceleration RMS 89 vs reference 2 rad/s^2
- 4.1 joint:shoulder_yaw:land - right_shoulder_yaw_joint: mean |err| 61 deg (signed +61), step 81: robot +0.28 vs ref -1.08 rad
- 3.9 jitter:wrist_pitch:settle - left_wrist_pitch_joint: joint acceleration RMS 104 vs reference 4 rad/s^2

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |1.00| rad (end -0.92), reference max |0.51|
- arm joints mean |err| 42 deg; worst: right_shoulder_yaw 88, left_shoulder_yaw 64, left_shoulder_pitch 48, right_elbow 41
- action change mean 0.081 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: right_wrist_yaw 25, right_hip_yaw 24, right_knee 22, left_shoulder_yaw 21
- feet off the floor (> 6 cm): left 145, right 145 of 145 steps
- land (steps 81-94): pelvis speed mean 0.63 m/s, last 0.47; drift 0.15 m
- settle (steps 95-114): pelvis speed mean 0.33 m/s, last 0.08; drift 0.08 m
- stand_after (steps 115-239): pelvis speed mean 0.08 m/s, last 0.00; drift 0.18 m

## F. Training-config audit (what the training actually ran)

- 30 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 3, decider terms: 0

## F2. Knobs this round trained with vs round 3 (3 differences)

- prior.lunge: - -> 3.0
- prior.support: - -> 2.0
- reference.variant: "plant_vlm_hold" -> "reachqp_vlm_hold"

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r3: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x780bb02813a0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r4: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7cfec9c694e0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds [nan, 0.016]), rounds used 4, GPU 3.9 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | True | == False | FAIL |
| hold_still_speed | eval.hold_pelvis_speed_max | 0.189 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.02 | <= 0.05 | pass |
| hold_no_sway | eval.hold_sway_m | 0.021 | <= 0.03 | pass |
| hold_torso_calm | eval.hold_torso_angvel_rms | 0.471 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.018 | <= 0.1 | pass |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 73.1 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.496 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.537 | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 200 | <= 0 | FAIL |
| post_no_fall | eval.post_fell | True | == False | FAIL |
| post_no_drift | eval.post_drift_m | 0.005 | <= 0.15 | pass |
| post_posture | eval.post_tilt_err_max_deg | 72.3 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 41.67 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 142.0 | >= 229.95000000000002 | FAIL |
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
