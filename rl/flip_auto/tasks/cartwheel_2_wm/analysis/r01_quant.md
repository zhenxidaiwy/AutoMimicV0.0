# Round 1 - quantitative report (step 1, before any diagnosis)

run `2026-11-04_16-17-39_cw2wm_r01`, best checkpoint `model_1809.pt` (score 2.0), evaluated: model_526.pt 0.954, model_1167.pt 0.661, model_1809.pt 2.0

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | - |  |
| post_s | 5.0 | - |  |
| robot_rotation_deg | 261.7 | - |  |
| robot_max_rotation_deg | 264.9 | - |  |
| robot_peak_pelvis_m | 0.768 | - |  |
| robot_airborne_s | 0.12 | - |  |
| landed_upright | False | - |  |
| end_tilt_deg | 97.7 | - |  |
| pelvis_rise_m | 0.014 | - |  |
| stand_stable | False | - |  |
| stand_feet_d_end | 0.547 | - |  |
| track_body_err_m | 0.6558 | - |  |
| track_joint_err | 3.5899 | - |  |
| post_fell | True | - |  |
| post_tilt_err_max_deg | 84.4 | - |  |
| post_drift_m | 0.287 | - |  |
| post_sway_m | 0.168 | - |  |
| post_pelvis_speed_max | 0.677 | - |  |
| post_action_change | 0.406 | - |  |
| post_feet_off_steps | 226 | - |  |
| hold_window_s | 2.0 | - |  |
| hold_fell | True | - |  |
| hold_tilt_err_max_deg | 84.8 | - |  |
| hold_height_err_m | 0.622 | - |  |
| hold_pose_err_rad | 0.485 | - |  |
| hold_pelvis_speed_max | 1.289 | - |  |
| hold_drift_m | 0.214 | - |  |
| hold_sway_m | 0.129 | - |  |
| hold_torso_angvel_rms | 3.82 | - |  |
| hold_action_change | 0.6568 | - |  |
| hold_feet_off_steps | 160 | - |  |
| early_fall | False | - |  |
| score | 2.0 | - |  |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_16-17-39_cw2wm_r01/eval/_post_auto_model_1809.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.755 | - |  |
| end_pelvis_m | 0.103 | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_16-17-39_cw2wm_r01/eval/flip_auto_model_1809.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.0 | 0.0 | 1.0 | [103.0, 168.9, 257.0] | [91.7, 101.2, 107.4] | [0.029, 0.398, 1.007] |
| dr | 0.0 | 0.0 | 1.0 | [103.5, 166.3, 255.5] | [91.6, 101.0, 106.9] | [0.087, 0.44, 0.938] |
| delay1 | 0.0 | 0.0 | 1.0 | [59.5, 121.9, 239.1] | [90.3, 99.8, 110.3] | [0.059, 0.427, 1.167] |
| delay2 | 0.0 | 0.0 | 1.0 | [42.0, 158.0, 270.4] | [94.9, 103.5, 114.6] | [0.089, 0.484, 1.156] |
| kp085 | 0.0 | 0.0 | 1.0 | [94.8, 174.1, 239.4] | [88.5, 99.0, 102.5] | [0.017, 0.29, 0.692] |

## B. Deviations per phase (severity = measured / tolerance; top 6 per phase)

**stand**: 25 of 53 measurements beyond tolerance

- 6.5 body:wrist_yaw - right_wrist_yaw_link: mean 0.52 m, max 0.83 m
- 6.0 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 90 deg (signed +90), step 15: robot +0.77 vs ref -1.85 rad
- 5.0 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 88 vs reference 1 rad/s^2
- 4.1 body:ankle_roll - left_ankle_roll_link: mean 0.32 m, max 0.43 m
- 3.8 body:elbow - right_elbow_link: mean 0.30 m, max 0.48 m
- 3.1 asymmetry:shoulder_yaw - left/right differ 32 deg vs reference 1 deg

**lunge**: 22 of 51 measurements beyond tolerance

- 9.2 body:wrist_yaw - right_wrist_yaw_link: mean 0.74 m, max 0.84 m
- 9.0 joint:shoulder_pitch - right_shoulder_pitch_joint: mean |err| 136 deg (signed +136), step 16: robot +0.78 vs ref -1.85 rad
- 5.5 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 96 vs reference 1 rad/s^2
- 5.2 body:elbow - right_elbow_link: mean 0.42 m, max 0.49 m
- 4.1 body:ankle_roll - right_ankle_roll_link: mean 0.33 m, max 0.84 m
- 3.3 body:knee - right_knee_link: mean 0.26 m, max 0.61 m

**support**: 33 of 51 measurements beyond tolerance

- 12.4 body:ankle_roll - right_ankle_roll_link: mean 0.99 m, max 1.39 m
- 8.7 body:knee - left_knee_link: mean 0.70 m, max 1.05 m
- 7.7 joint:shoulder_pitch - left_shoulder_pitch_joint: mean |err| 115 deg (signed +115), step 80: robot +0.28 vs ref -2.10 rad
- 5.8 body:wrist_yaw - left_wrist_yaw_link: mean 0.46 m, max 0.67 m
- 5.4 body:hip_roll - left_hip_roll_link: mean 0.43 m, max 0.65 m
- 4.9 asymmetry:hip_yaw - left/right differ 62 deg vs reference 14 deg

**land**: 42 of 53 measurements beyond tolerance

- 12.5 jitter:wrist_roll - left_wrist_roll_joint: joint acceleration RMS 213 vs reference 1 rad/s^2
- 10.7 body:ankle_roll - left_ankle_roll_link: mean 0.86 m, max 1.00 m
- 10.5 body:shoulder_roll - left_shoulder_roll_link: mean 0.84 m, max 0.96 m
- 10.3 body:wrist_yaw - left_wrist_yaw_link: mean 0.82 m, max 0.94 m
- 9.5 body:elbow - left_elbow_link: mean 0.76 m, max 0.83 m
- 8.2 body:knee - left_knee_link: mean 0.65 m, max 0.76 m

**settle**: 45 of 54 measurements beyond tolerance

- 16.6 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 462 vs reference 4 rad/s^2
- 16.0 body:wrist_yaw - right_wrist_yaw_link: mean 1.28 m, max 1.37 m
- 13.4 body:elbow - right_elbow_link: mean 1.08 m, max 1.18 m
- 13.2 jitter:all - mean action change 0.658 (quiet < 0.05)
- 12.3 body:shoulder_roll - left_shoulder_roll_link: mean 0.99 m, max 1.04 m
- 10.9 body:ankle_roll - left_ankle_roll_link: mean 0.88 m, max 1.12 m

**stand_after**: 44 of 54 measurements beyond tolerance

- 17.9 body:wrist_yaw - left_wrist_yaw_link: mean 1.43 m, max 1.46 m
- 15.6 jitter:knee - left_knee_joint: joint acceleration RMS 378 vs reference 3 rad/s^2
- 15.5 jitter:ankle_pitch - left_ankle_pitch_joint: joint acceleration RMS 413 vs reference 4 rad/s^2
- 14.6 body:elbow - right_elbow_link: mean 1.17 m, max 1.21 m
- 12.7 jitter:all - mean action change 0.635 (quiet < 0.05)
- 12.2 body:shoulder_roll - left_shoulder_roll_link: mean 0.97 m, max 1.00 m

## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 1.5 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.27 |
| 1.3 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.328 |
| 3.1 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 0.0692 |
| 1.7 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 0.221 |
| 1.0 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.413 |
| 1.3 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.317 |
| 2.3 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0.139 |
| 1.5 | cartwheel_2/joint:waist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.275 |
| 1.5 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0.264 |
| 4.1 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 0.0373 |
| 9.2 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 0.00062 |
| 3.3 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 0.0708 |
| 2.0 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.178 |
| 2.7 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0.0945 |
| 1.3 | cartwheel_2/asymmetry:elbow:lunge | dyn_sym | 0.0 | 0.2 | 0.314 |
| 3.2 | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | 0.0612 |
| 2.8 | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | 0.0872 |
| 3.0 | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | 0.0732 |
| 4.3 | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0226 |
| 3.3 | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | 0.0548 |
| 7.7 | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | 0.00126 |
| 3.5 | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | 0.0481 |
| 2.1 | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | 0.167 |
| 1.7 | cartwheel_2/joint:waist_pitch:support | dyn_joint | 0.0 | 0.3 | 0.221 |
| 1.2 | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | 0.366 |
| 3.1 | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | 0.0646 |
| 4.4 | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | 0.0207 |
| 12.4 | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | 4.79e-05 |
| 5.8 | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | 0.00961 |
| 8.7 | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | 0.000935 |
| 3.6 | cartwheel_2/asymmetry:elbow:support | dyn_sym | 0.0 | 0.2 | 0.0449 |
| 3.6 | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | 0.0417 |
| 1.2 | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | 0.35 |
| 1.1 | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | 0.378 |
| 10.7 | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | 0.000191 |
| 10.3 | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | 0.000264 |
| 8.2 | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | 0.00147 |
| 2.2 | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | 0.143 |
| 1.2 | cartwheel_2/asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | 0.366 |
| 4.7 | cartwheel_2/contact:right_foot:land | dyn_contact | 0.0 | None | - |
| 1.9 | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.184 |
| 4.2 | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | 0.0255 |
| 1.6 | cartwheel_2/joint:knee:settle | dyn_joint | 0.0 | 0.3 | 0.258 |
| 3.0 | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | 0.0713 |
| 2.7 | cartwheel_2/asymmetry:ankle_pitch:settle | dyn_sym | 0.0 | 0.2 | 0.0916 |
| 6.3 | cartwheel_2/asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | 0.0041 |
| 7.5 | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | 0.00148 |
| 3.7 | cartwheel_2/contact:left_foot:settle | dyn_contact | 0.0 | None | - |
| 4.3 | cartwheel_2/contact:right_foot:settle | dyn_contact | 0.0 | None | - |
| 13.2 | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| 1.8 | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.212 |
| 5.4 | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.00868 |
| 5.0 | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.0125 |
| 4.6 | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | 0.0173 |
| 10.0 | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | 0.000158 |
| 2.0 | cartwheel_2/contact:left_foot:stand_after | dyn_contact | 0.0 | None | - |
| 12.7 | cartwheel_2/jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 17.9 | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | 6.21e-07 |
| 9.0 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0.000372 |
| 16.0 | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | 2.76e-06 |
| 14.6 | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | 8.68e-06 |
| 10.9 | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | 0.000158 |
| 13.4 | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | 2.13e-05 |
| 15.6 | cartwheel_2/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 8.0 | cartwheel_2/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 12.3 | cartwheel_2/body:shoulder_roll:settle | dyn_body | 0.0 | 0.1 | 5.12e-05 |
| 12.2 | cartwheel_2/body:shoulder_roll:stand_after | dyn_body | 0.0 | 0.1 | 5.97e-05 |
| 7.2 | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | 0.00192 |
| 8.9 | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | 0.000798 |
| 1.6 | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | 0.246 |
| 8.0 | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 5.0 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| 12.5 | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| 4.0 | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | 0.0407 |
| 5.5 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| 1.3 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.346 |
| 2.2 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.147 |
| 4.1 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.0389 |
| 6.5 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.00555 |
| 4.9 | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.5 | 0.184 |
| 1.9 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| 2.7 | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | 0.095 |
| 5.1 | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| 3.6 | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.6 | 0.35 |
| 2.2 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.148 |
| 16.6 | cartwheel_2/jitter:wrist_roll:settle | dyn_quiet | 0.0 | 1.0 | - |
| 15.5 | cartwheel_2/jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 10.9 | cartwheel_2/jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 10.5 | cartwheel_2/body:shoulder_roll:land | dyn_body | 0.0 | 0.1 | 0.000233 |
| 9.5 | cartwheel_2/jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| 9.5 | cartwheel_2/body:elbow:land | dyn_body | 0.0 | 0.1 | 0.000521 |

91 of 113 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 70

- 8.2 body:torso:stand_after - torso_link: mean 0.66 m, max 0.68 m
- 8.1 body:torso:settle - torso_link: mean 0.65 m, max 0.67 m
- 7.9 jitter:waist_yaw:stand_after - waist_yaw_joint: joint acceleration RMS 155 vs reference 2 rad/s^2
- 7.9 jitter:hip_roll:stand_after - left_hip_roll_joint: joint acceleration RMS 177 vs reference 2 rad/s^2
- 7.8 body:pelvis:stand_after - pelvis: mean 0.63 m, max 0.65 m
- 7.7 body:pelvis:settle - pelvis: mean 0.62 m, max 0.63 m
- 7.4 jitter:wrist_pitch:land - left_wrist_pitch_joint: joint acceleration RMS 161 vs reference 2 rad/s^2
- 7.4 body:hip_roll:stand_after - right_hip_roll_link: mean 0.59 m, max 0.62 m
- 7.4 jitter:wrist_yaw:settle - left_wrist_yaw_joint: joint acceleration RMS 121 vs reference 0 rad/s^2
- 7.2 body:torso:land - torso_link: mean 0.58 m, max 0.62 m
- 7.0 body:hip_roll:settle - left_hip_roll_link: mean 0.56 m, max 0.60 m
- 7.0 jitter:waist_roll:stand_after - waist_roll_joint: joint acceleration RMS 174 vs reference 3 rad/s^2
- 7.0 body:knee:settle - right_knee_link: mean 0.56 m, max 0.82 m
- 6.7 body:hip_roll:land - left_hip_roll_link: mean 0.54 m, max 0.61 m
- 6.5 body:pelvis:land - pelvis: mean 0.52 m, max 0.56 m

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |0.62| rad (end -0.10), reference max |0.51|
- arm joints mean |err| 35 deg; worst: right_shoulder_roll 78, right_shoulder_yaw 45, right_elbow 44, left_elbow 37
- action change mean 0.636 (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: left_knee 336, left_ankle_pitch 310, right_knee 254, left_hip_pitch 161
- feet off the floor (> 6 cm): left 131, right 95 of 145 steps
- land (steps 81-94): pelvis speed mean 1.16 m/s, last 0.38; drift 0.25 m
- settle (steps 95-114): pelvis speed mean 0.26 m/s, last 0.19; drift 0.05 m
- stand_after (steps 115-239): pelvis speed mean 0.46 m/s, last 0.39; drift 0.22 m

## F. Training-config audit (what the training actually ran)

- 0 reward terms in the log; flip_* terms of the current code missing from training: ['flip_pushoff', 'flip_lean', 'flip_spin', 'flip_airborne', 'flip_height', 'flip_land', 'flip_plane_axis', 'flip_plane_rate', 'flip_leg_sym', 'flip_leg_track', 'flip_leg_calm', 'flip_feet_together', 'flip_tuck', 'flip_rot_track', 'flip_land_balance', 'flip_stay_down', 'flip_stand_still', 'flip_stand_quiet']
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 3, decider terms: 0

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds []), rounds used 1, GPU 1.0 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | True | == False | FAIL |
| hold_still_speed | eval.hold_pelvis_speed_max | 1.289 | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | 0.214 | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | 0.129 | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | 3.82 | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | 0.657 | <= 0.1 | FAIL |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 84.8 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | 0.485 | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | 0.622 | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 160 | <= 0 | FAIL |
| post_no_fall | eval.post_fell | True | == False | FAIL |
| post_no_drift | eval.post_drift_m | 0.287 | <= 0.15 | FAIL |
| post_posture | eval.post_tilt_err_max_deg | 84.4 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 17.86 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 261.7 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | False | == True | FAIL |

worst unwaived library check: cartwheel_2/body:wrist_yaw:stand_after

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
