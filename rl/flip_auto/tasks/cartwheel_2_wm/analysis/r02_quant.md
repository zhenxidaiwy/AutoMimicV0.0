# Round 2 - quantitative report (step 1, before any diagnosis)

run `2026-11-04_17-30-08_cw2wm_r02`, best checkpoint `model_531.pt` (score nan), evaluated: model_531.pt nan, model_1175.pt nan, model_1816.pt nan

## A. Evaluation metrics (best checkpoint) vs previous round

| metric | this | previous | change |
|---|---|---|---|
| clip_s | 9.8 | 9.8 | +0 |
| post_s | 5.0 | 5.0 | +0 |
| robot_rotation_deg | 472.8 | 261.7 | +211 |
| robot_max_rotation_deg | 616.0 | 264.9 | +351 |
| robot_peak_pelvis_m | 8.456 | 0.768 | +7.69 |
| robot_airborne_s | 0.38 | 0.12 | +0.26 |
| landed_upright | False | False |  |
| end_tilt_deg | 0.0 | 97.7 | -97.7 |
| pelvis_rise_m | 5.615 | 0.014 | +5.6 |
| stand_stable | False | False |  |
| stand_feet_d_end | nan | 0.547 | +nan |
| track_body_err_m | nan | 0.6558 | +nan |
| track_joint_err | nan | 3.5899 | +nan |
| post_fell | False | True |  |
| post_tilt_err_max_deg | 19.9 | 84.4 | -64.5 |
| post_drift_m | nan | 0.287 | +nan |
| post_sway_m | nan | 0.168 | +nan |
| post_pelvis_speed_max | nan | 0.677 | +nan |
| post_action_change | nan | 0.406 | +nan |
| post_feet_off_steps | 0 | 226 | -226 |
| hold_window_s | 2.0 | 2.0 | +0 |
| hold_fell | False | True |  |
| hold_tilt_err_max_deg | 19.9 | 84.8 | -64.9 |
| hold_height_err_m | nan | 0.622 | +nan |
| hold_pose_err_rad | nan | 0.485 | +nan |
| hold_pelvis_speed_max | nan | 1.289 | +nan |
| hold_drift_m | nan | 0.214 | +nan |
| hold_sway_m | nan | 0.129 | +nan |
| hold_torso_angvel_rms | nan | 3.82 | +nan |
| hold_action_change | nan | 0.6568 | +nan |
| hold_feet_off_steps | 0 | 160 | -160 |
| early_fall | False | False |  |
| score | nan | 2.0 | +nan |
| motion | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_17-30-08_cw2wm_r02/eval/_post_auto_model_531.npz | - |  |
| ref_rotation_deg | 255.5 | - |  |
| ref_peak_pelvis_m | 0.751 | - |  |
| end_pelvis_m | nan | - |  |
| video | /home/user/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-11-04_17-30-08_cw2wm_r02/eval/flip_auto_model_531.mp4 | - |  |

## A2. Robustness (success = rotation >= 0.9 x the reference's own rotation and, over the run past the reference, upright, pelvis > 0.6 m, drift < 0.3 m (v1) / < 0.5 m under pushes (v2, gates))

| scenario | success v2 | success v1 | fell | rotation p5/50/95 | end tilt p5/50/95 | drift p5/50/95 |
|---|---|---|---|---|---|---|
| nominal | 0.0 | 0.0 | 0.27 | [298.0, 840.4, 1943.9] | [0.0, 0.0, 116.9] | [nan, nan, nan] |
| dr | 0.0 | 0.0 | 0.281 | [345.5, 783.2, 1800.9] | [0.0, 0.0, 122.4] | [nan, nan, nan] |
| delay1 | 0.0 | 0.0 | 0.441 | [312.6, 741.2, 1883.7] | [0.0, 0.0, 122.6] | [nan, nan, nan] |
| delay2 | 0.0 | 0.0 | 0.641 | [260.8, 589.3, 1447.8] | [0.0, 82.5, 126.0] | [nan, nan, nan] |
| kp085 | 0.0 | 0.0 | 0.246 | [291.0, 800.3, 1850.9] | [0.0, 0.0, 122.4] | [nan, nan, nan] |

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

**stand**: 52 of 53 measurements beyond tolerance

- 234.3 jitter:shoulder_roll - right_shoulder_roll_joint: joint acceleration RMS 6174 vs reference 4 rad/s^2
- 219.1 jitter:shoulder_yaw - right_shoulder_yaw_joint: joint acceleration RMS 7715 vs reference 7 rad/s^2
- 161.4 jitter:wrist_yaw - left_wrist_yaw_joint: joint acceleration RMS 2811 vs reference 1 rad/s^2
- 109.3 jitter:elbow - right_elbow_joint: joint acceleration RMS 8824 vs reference 22 rad/s^2
- 104.0 jitter:wrist_pitch - left_wrist_pitch_joint: joint acceleration RMS 3645 vs reference 7 rad/s^2
- 102.5 jitter:wrist_roll - right_wrist_roll_joint: joint acceleration RMS 1792 vs reference 1 rad/s^2

**lunge**: 51 of 51 measurements beyond tolerance

- 64159.3 asymmetry:elbow - left/right differ 641596 deg vs reference 3 deg
- 36793.4 joint:elbow - right_elbow_joint: mean |err| 551901 deg (signed -551901), step 45: robot -27747.41 vs ref +0.81 rad
- 34673.5 asymmetry:shoulder_yaw - left/right differ 346743 deg vs reference 8 deg
- 30993.1 asymmetry:shoulder_roll - left/right differ 309946 deg vs reference 15 deg
- 29708.9 joint:shoulder_yaw - right_shoulder_yaw_joint: mean |err| 445633 deg (signed +445633), step 45: robot +22130.53 vs ref -0.49 rad
- 23982.0 joint:wrist_pitch - left_wrist_pitch_joint: mean |err| 359730 deg (signed +359730), step 45: robot +18187.57 vs ref +0.61 rad

**support**: 0 of 51 measurements beyond tolerance


**land**: 0 of 53 measurements beyond tolerance


**settle**: 0 of 54 measurements beyond tolerance


**stand_after**: 0 of 54 measurements beyond tolerance


## C. Library checks that fail, with the effective signal of their fix

signal = exp(-measured / std) of the fix's own reward at the measured error (dyn_joint / dyn_sym in rad, dyn_body in m);
an active fix with signal < 0.05 gives the policy practically no gradient.

| severity | check | fix | weight | std | signal |
|---|---|---|---|---|---|
| 5.8 | cartwheel_2/joint:elbow:stand | dyn_joint | 0.0 | 0.3 | 0.00627 |
| 32.5 | cartwheel_2/asymmetry:hip_yaw:stand | dyn_sym | 0.0 | 0.2 | 4.64e-13 |
| 5.0 | cartwheel_2/asymmetry:ankle_roll:stand | dyn_sym | 0.0 | 0.2 | 0.0123 |
| 12.6 | cartwheel_2/asymmetry:shoulder_pitch:stand | dyn_sym | 0.0 | 0.2 | 1.69e-05 |
| 24.0 | cartwheel_2/asymmetry:shoulder_yaw:stand | dyn_sym | 0.0 | 0.2 | 7.8e-10 |
| 2.4 | cartwheel_2/asymmetry:elbow:stand | dyn_sym | 0.0 | 0.2 | 0.125 |
| 26.0 | cartwheel_2/asymmetry:wrist_roll:stand | dyn_sym | 0.0 | 0.2 | 1.35e-10 |
| 5.0 | cartwheel_2/contact:left_foot:stand | dyn_contact | 1.0 | None | - |
| 5.3 | cartwheel_2/contact:right_foot:stand | dyn_contact | 0.0 | None | - |
| 218.2 | cartwheel_2/joint:ankle_pitch:lunge | dyn_joint | 0.0 | 0.3 | 1.97e-83 |
| 3992.3 | cartwheel_2/joint:hip_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 4970.4 | cartwheel_2/joint:knee:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 2921.9 | cartwheel_2/joint:waist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 631.6 | cartwheel_2/joint:waist_roll:lunge | dyn_joint | 0.0 | 0.3 | 4.07e-240 |
| 2840.5 | cartwheel_2/joint:wrist_roll:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 6006.6 | cartwheel_2/joint:wrist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 251.1 | cartwheel_2/body:ankle_roll:lunge | dyn_body | 0.0 | 0.1 | 5.81e-88 |
| 244.5 | cartwheel_2/body:wrist_yaw:lunge | dyn_body | 0.0 | 0.1 | 1.12e-85 |
| 250.0 | cartwheel_2/body:knee:lunge | dyn_body | 0.0 | 0.1 | 1.34e-87 |
| 2656.9 | cartwheel_2/asymmetry:hip_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| 60.1 | cartwheel_2/asymmetry:ankle_roll:lunge | dyn_sym | 0.0 | 0.2 | 1.68e-23 |
| 34673.5 | cartwheel_2/asymmetry:shoulder_yaw:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| 64159.3 | cartwheel_2/asymmetry:elbow:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| 4492.0 | cartwheel_2/asymmetry:wrist_roll:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| nan | cartwheel_2/joint:ankle_pitch:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:hip_pitch:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:hip_roll:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:hip_yaw:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:knee:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:shoulder_pitch:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:shoulder_roll:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:shoulder_yaw:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:waist_pitch:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:waist_roll:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:wrist_roll:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:wrist_yaw:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/body:ankle_roll:support | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:wrist_yaw:support | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:knee:support | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/asymmetry:ankle_roll:support | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:elbow:support | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/joint:ankle_pitch:land | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:wrist_roll:land | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:wrist_yaw:land | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/body:ankle_roll:land | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:wrist_yaw:land | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:knee:land | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/asymmetry:hip_yaw:land | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:elbow:land | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/joint:ankle_pitch:settle | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:hip_pitch:settle | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/joint:knee:settle | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/asymmetry:hip_yaw:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:ankle_pitch:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:ankle_roll:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:shoulder_roll:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:elbow:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:wrist_roll:settle | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/jitter:all:settle | dyn_quiet | 1.0 | 1.0 | - |
| nan | cartwheel_2/asymmetry:hip_roll:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:hip_yaw:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:ankle_roll:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:shoulder_roll:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:shoulder_yaw:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:elbow:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:wrist_roll:stand_after | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/jitter:all:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/body:wrist_yaw:stand_after | dyn_body | 0.0 | 0.1 | nan |
| 21081.7 | cartwheel_2/joint:shoulder_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| nan | cartwheel_2/body:wrist_yaw:settle | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:elbow:stand_after | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:ankle_roll:settle | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:elbow:settle | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/jitter:knee:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/jitter:hip_yaw:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/body:shoulder_roll:settle | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/body:shoulder_roll:stand_after | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/joint:shoulder_pitch:land | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/body:ankle_roll:stand_after | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/joint:elbow:support | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/jitter:ankle_roll:land | dyn_quiet | 0.0 | 1.0 | - |
| 102.5 | cartwheel_2/jitter:wrist_roll:stand | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/jitter:wrist_roll:land | dyn_quiet | 1.0 | 1.0 | - |
| nan | cartwheel_2/body:elbow:support | dyn_body | 0.0 | 0.1 | nan |
| 841.3 | cartwheel_2/jitter:wrist_roll:lunge | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/asymmetry:shoulder_yaw:land | dyn_sym | 0.0 | 0.2 | nan |
| 8.0 | cartwheel_2/body:knee:stand | dyn_body | 0.0 | 0.1 | 0.00169 |
| 4.5 | cartwheel_2/joint:knee:stand | dyn_joint | 0.0 | 0.3 | 0.0194 |
| 11.1 | cartwheel_2/body:ankle_roll:stand | dyn_body | 0.0 | 0.1 | 0.000144 |
| 6.2 | cartwheel_2/body:wrist_yaw:stand | dyn_body | 0.0 | 0.1 | 0.00723 |
| nan | cartwheel_2/asymmetry:hip_yaw:support | dyn_sym | 0.0 | 0.5 | nan |
| 219.1 | cartwheel_2/jitter:shoulder_yaw:stand | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/asymmetry:hip_pitch:support | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/joint:hip_pitch:land | dyn_joint | 0.0 | 0.3 | nan |
| nan | cartwheel_2/jitter:shoulder_yaw:land | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/asymmetry:shoulder_yaw:support | dyn_sym | 0.0 | 0.2 | nan |
| nan | cartwheel_2/asymmetry:wrist_roll:support | dyn_sym | 0.0 | 0.6 | nan |
| 5.5 | cartwheel_2/joint:ankle_pitch:stand | dyn_joint | 0.0 | 0.3 | 0.00844 |
| 30993.1 | cartwheel_2/asymmetry:shoulder_roll:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| nan | cartwheel_2/jitter:wrist_roll:settle | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/jitter:ankle_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/jitter:wrist_roll:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/body:shoulder_roll:land | dyn_body | 0.0 | 0.1 | nan |
| nan | cartwheel_2/jitter:hip_pitch:stand_after | dyn_quiet | 0.0 | 1.0 | - |
| nan | cartwheel_2/body:elbow:land | dyn_body | 0.0 | 0.1 | nan |
| 36793.4 | cartwheel_2/joint:elbow:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 29708.9 | cartwheel_2/joint:shoulder_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 23982.0 | cartwheel_2/joint:wrist_pitch:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 22148.5 | cartwheel_2/joint:shoulder_roll:lunge | dyn_joint | 0.0 | 0.3 | 0 |
| 21968.6 | cartwheel_2/asymmetry:shoulder_pitch:lunge | dyn_sym | 0.0 | 0.2 | 0 |
| 13066.3 | cartwheel_2/joint:waist_yaw:lunge | dyn_joint | 0.0 | 0.3 | 0 |

40 of 119 checks of task cartwheel_2 fail.

## D. Deviations no check covers yet (severity > 2): 60

- 9305.4 asymmetry:hip_roll:lunge - left/right differ 93083 deg vs reference 29 deg
- 6867.7 asymmetry:knee:lunge - left/right differ 68718 deg vs reference 41 deg
- 4800.2 joint:hip_roll:lunge - left_hip_roll_joint: mean |err| 72002 deg (signed -71998), step 45: robot -3644.28 vs ref +0.47 rad
- 2846.5 jitter:shoulder_yaw:lunge - right_shoulder_yaw_joint: joint acceleration RMS 120936 vs reference 9 rad/s^2
- 2474.6 asymmetry:hip_pitch:lunge - left/right differ 24810 deg vs reference 64 deg
- 1549.0 joint:hip_yaw:lunge - right_hip_yaw_joint: mean |err| 23235 deg (signed -23227), step 45: robot -1195.19 vs ref -0.17 rad
- 1462.0 jitter:wrist_yaw:lunge - right_wrist_yaw_joint: joint acceleration RMS 25365 vs reference 1 rad/s^2
- 1261.3 jitter:waist_yaw:lunge - waist_yaw_joint: joint acceleration RMS 56333 vs reference 10 rad/s^2
- 1010.0 jitter:shoulder_roll:lunge - right_shoulder_roll_joint: joint acceleration RMS 94646 vs reference 26 rad/s^2
- 688.8 jitter:shoulder_pitch:lunge - right_shoulder_pitch_joint: joint acceleration RMS 88669 vs reference 38 rad/s^2
- 574.2 jitter:wrist_pitch:lunge - left_wrist_pitch_joint: joint acceleration RMS 103627 vs reference 55 rad/s^2
- 495.8 jitter:elbow:lunge - right_elbow_joint: joint acceleration RMS 156788 vs reference 100 rad/s^2
- 386.9 asymmetry:ankle_pitch:lunge - left/right differ 3904 deg vs reference 35 deg
- 263.2 jitter:hip_roll:lunge - left_hip_roll_joint: joint acceleration RMS 20677 vs reference 21 rad/s^2
- 248.4 body:hip_roll:lunge - right_hip_roll_link: mean 19.87 m, max 102.82 m

## E. After landing (settle + stand_after, robot vs reference)

- waist_yaw: robot max |nan| rad (end +nan), reference max |0.51|
- arm joints mean |err| nan deg; worst: left_shoulder_pitch nan, left_shoulder_roll nan, left_shoulder_yaw nan, left_elbow nan
- action change mean nan (quiet < 0.05)
- joint acceleration mean (rad/s^2), worst: waist_pitch nan, right_wrist_yaw nan, right_wrist_pitch nan, right_wrist_roll nan
- feet off the floor (> 6 cm): left 0, right 0 of 145 steps
- land (steps 81-94): pelvis speed mean nan m/s, last nan; drift nan m
- settle (steps 95-114): pelvis speed mean nan m/s, last nan; drift nan m
- stand_after (steps 115-239): pelvis speed mean nan m/s, last nan; drift nan m

## F. Training-config audit (what the training actually ran)

- 30 reward terms in the log; flip_* terms of the current code missing from training: none
- root orientation term: flip_root_ori (replaced)
- flip terminations: {'term_flight_spread': None, 'term_hip_extended': {'max_hip': 1.2}, 'term_stand_fail': {'max_d': 0.85, 'max_tilt': 40.0, 'max_waist': 0.6}, 'term_leg_twist': None}
- active library fixes: 3, decider terms: 0

## F2. Knobs this round trained with vs round 1 (4 differences)

- reference.labels: - -> "labels_hold_50fps.npz"
- reference.variant: - -> "plant_vlm_hold"
- weights.flip_land_balance: 2.0 -> 0.0
- weights.flip_leg_sym: 1.0 -> 0.0

Training-log configuration lines that differ (ground truth):

- [train_dance] ee_body_pos termination: r1: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x709fc7fc8cc0>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
  r2: TerminationTermCfg(func=<function bad_motion_body_pos_z_only at 0x7bf4591d4d60>, params={'command_name': 'motion', 'threshold': 0.6, 'body_names': ('left_ankle_roll_link', 'right_ankle_roll_link', 'left_wrist_yaw_link', 'right_wrist_yaw_link')}, time_out=False
- [train_dance] flip rewards x2.0: r1: {'flip_pushoff': 4.0, 'flip_lean': 2.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 2.0, 'flip_plane_axis': 3.0, 'flip_plane_rate': 2.0, 'flip_leg_sym': 2.0, 'flip_leg_track': 2.0, 'flip_leg_calm': 1.0, 'flip_feet_together': 4.0, '
  r2: {'flip_pushoff': 4.0, 'flip_lean': 2.0, 'flip_spin': 6.0, 'flip_airborne': 3.0, 'flip_height': 2.0, 'flip_land': 2.0, 'flip_plane_axis': 3.0, 'flip_plane_rate': 2.0, 'flip_leg_sym': 0.0, 'flip_leg_track': 2.0, 'flip_leg_calm': 1.0, 'flip_feet_together': 4.0, '

## S. Stop criteria (generic + family:hand_support + task; stop_criteria.json)

**not done** - converged: False (rel. improvement of the last rounds []), rounds used 2, GPU 2.0 h, over budget: False, waivers in force: 0

| gate | metric | value | threshold | status |
|---|---|---|---|---|
| hold_window_2s | eval.hold_window_s | 2.0 | >= 2.0 | pass |
| hold_no_fall | eval.hold_fell | False | == False | pass |
| hold_still_speed | eval.hold_pelvis_speed_max | nan | <= 0.15 | FAIL |
| hold_no_drift | eval.hold_drift_m | nan | <= 0.05 | FAIL |
| hold_no_sway | eval.hold_sway_m | nan | <= 0.03 | FAIL |
| hold_torso_calm | eval.hold_torso_angvel_rms | nan | <= 0.2 | FAIL |
| hold_quiet | eval.hold_action_change | nan | <= 0.1 | FAIL |
| hold_posture_tilt | eval.hold_tilt_err_max_deg | 19.9 | <= 5 | FAIL |
| hold_posture_joints | eval.hold_pose_err_rad | nan | <= 0.15 | FAIL |
| hold_posture_height | eval.hold_height_err_m | nan | <= 0.05 | FAIL |
| hold_feet_down | eval.hold_feet_off_steps | 0 | <= 0 | pass |
| post_no_fall | eval.post_fell | False | == False | pass |
| post_no_drift | eval.post_drift_m | nan | <= 0.15 | FAIL |
| post_posture | eval.post_tilt_err_max_deg | 19.9 | <= 10 | FAIL |
| critic_clean | critic.max_unwaived_severity | 64159.3 | <= 3.0 | FAIL |
| robust_training_dr | robust.dr | 0.0 | >= 0.95 | FAIL |
| robust_latency_20ms | robust.delay1 | 0.0 | >= 0.95 | FAIL |
| robust_stiffness | robust.kp085 | 0.0 | >= 0.95 | FAIL |
| sim2sim_nominal | sim2sim.nominal | None | >= 0.95 | pending |
| sim2sim_latency_20ms | sim2sim.delay20 | None | >= 0.95 | pending |
| rotation_complete | eval.robot_rotation_deg | 472.8 | >= 229.95000000000002 | pass |
| landed_upright | eval.landed_upright | False | == True | FAIL |

worst unwaived library check: cartwheel_2/asymmetry:elbow:lunge

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
