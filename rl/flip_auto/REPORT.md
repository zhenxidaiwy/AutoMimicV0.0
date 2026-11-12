# Backflip auto harness (G1 EDU limits: knee 120 N.m)

| round | train min | ep len | best ckpt | score | rotation deg (max) | pelvis rise m | airborne s | landed | out-of-plane deg (mean/max) | legs asym/err deg | feet dist max/touchdown m | adjustment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | None | 234.61 | model_1000.pt | 4.163 | 322.8 (347.3) | 0.641 | 0.8 | False | 52.4/80.0 | 25.1/39.2 | None/None | training killed at ~1400 iters (operator error); model_1000 used; rotates but does not land -> land x1.5, land prior x1.3; out of plane (max 80.0 deg) -> plane weights x1.5; legs flail (asym 25.1 deg, err 39.2 deg) -> leg weights x1.5 |
| 2 | 66.2 | 86.12 | model_2499.pt | 5.442 | 321.2 (360.0) | 0.628 | 0.78 | False | 18.5/33.4 | 4.4/41.9 | None/None | rotates but does not land -> land x1.5, land prior x1.3; out of plane (max 33.4 deg) -> plane weights x1.5; legs flail (asym 4.4 deg, err 41.9 deg) -> leg weights x1.5 |
| 3 | 64.7 | 122.55 | model_3500.pt | 5.768 | 478.7 (480.3) | 0.624 | 0.78 | False | 3.7/6.7 | 4.5/44.0 | 1.318/0.117 | rotates but does not land -> land x1.5, land prior x1.3; legs flail (asym 4.5 deg, err 44.0 deg) -> leg weights x1.5; took off 6 steps early -> stay-down x1.5; hips not tucked in flight (err 3.78 rad) -> tuck x1.5; collapsed after landing (pelvis 0.207 m) -> land-balance x1.5; legs spread (feet 1.318 m) -> feet-together x1.5 |
| 4 | 65.6 | 341.21 | model_4000.pt | 7.621 | 368.3 (378.9) | 0.647 | 0.68 | True | 7.9/12.5 | 6.1/43.7 | 1.243/0.112 | full flip landed -> keep knobs, train on; legs flail (asym 6.1 deg, err 43.7 deg) -> leg weights x1.5; took off 6 steps early -> stay-down x1.5; hips not tucked in flight (err 3.69 rad) -> tuck x1.5; legs spread (feet 1.243 m) -> feet-together x1.5 |
| 5 | 65.9 | 279.67 | model_4500.pt | 7.714 | 365.8 (375.4) | 0.607 | 0.62 | True | 5.8/9.2 | 4.7/41.6 | 1.27/0.161 | full flip landed -> keep knobs, train on; legs flail (asym 4.7 deg, err 41.6 deg) -> leg weights x1.5; took off 5 steps early -> stay-down x1.5; hips not tucked in flight (err 3.57 rad) -> tuck x1.5; legs spread (feet 1.27 m) -> feet-together x1.5 |
| 6 | 69.8 | 243.21 | model_5999.pt | 6.816 | 387.2 (388.9) | 0.463 | 0.62 | True | 4.7/7.6 | 2.4/30.4 | 0.374/0.188 | full flip landed -> keep knobs, train on; legs flail (asym 2.4 deg, err 30.4 deg) -> leg weights x1.5; took off 5 steps early -> stay-down x1.5; hips not tucked in flight (err 1.06 rad) -> tuck x1.5; hips extended -> hip limit 0.9 rad; not standing stably (feet end 0.231 m) -> stand limits 0.45 m / 30.0 deg; legs spread (feet 0.374 m) -> feet-together x1.5 |
| 7 | 70.5 | 205.59 | model_5000.pt | 8.783 | 372.9 (373.4) | 0.437 | 0.6 | True | 6.0/11.5 | 2.5/26.8 | 0.378/0.173 | fell before take-off -> lean x1.5, stand/crouch prior x1.3; legs flail (asym 2.5 deg, err 26.8 deg) -> leg weights x1.5; took off 5 steps early -> stay-down x1.5; hips not tucked in flight (err 0.98 rad) -> tuck x1.5; hips extended -> hip limit 0.6 rad; legs spread (feet 0.378 m) -> feet-together x1.5 |
| 8 | 71.1 | 305.0 | model_5500.pt | 9.097 | 344.2 (370.8) | 0.574 | 0.74 | True | 7.6/18.5 | 4.7/19.6 | 0.322/0.241 | full flip landed -> keep knobs, train on; took off 5 steps early -> stay-down x1.5; flow complete -> fidelity stage 1: tracking x2.25, std x0.722 (body err 0.1444 m); knees over-folded by 2.06 rad (legs coiled) -> tuck x1.5 |
| 9 | 77.0 | 367.23 | model_6999.pt | 9.248 | 358.3 (367.2) | 0.436 | 0.58 | True | 7.7/17.0 | 3.0/6.4 | 0.228/0.201 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x3.375, std x0.614 (body err 0.1202 m); (suggestion) not quiet after landing (arm 2.962 rad/s, torso 1.805 rad/s, action change 0.4655) -> quiet x1.5 |
| 10 | 79.8 | 415.6 | model_8000.pt | 7.414 | 353.2 (361.2) | 0.389 | 0.58 | True | 4.8/9.1 | 1.9/5.1 | 0.232/0.203 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x2.25, std x0.722 (body err 0.104 m); (suggestion) not quiet after landing (arm 1.529 rad/s, torso 0.766 rad/s, action change 0.1416) -> quiet x1.5; (suggestion) not standing stably (feet end 0.349 m) -> stand limits 0.405 m / 25.0 deg |
| 11 | 80.5 | 448.61 | model_9499.pt | 9.433 | 371.2 (371.4) | 0.421 | 0.58 | True | 3.2/5.3 | 2.2/4.9 | 0.218/0.198 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x2.25, std x0.722 (body err 0.1056 m); (suggestion) not quiet after landing (arm 2.219 rad/s, torso 1.353 rad/s, action change 0.368) -> quiet x1.5 |
| 12 | 80.4 | 477.22 | model_10000.pt | 9.519 | 367.9 (367.9) | 0.3 | 0.56 | True | 4.4/9.1 | 1.6/6.2 | 0.215/0.196 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x2.25, std x0.722 (body err 0.0825 m); (suggestion) not quiet after landing (arm 0.676 rad/s, torso 0.466 rad/s, action change 0.0507) -> quiet x1.5 |
| 13 | 81.3 | 459.07 | model_11499.pt | 9.55 | 366.9 (367.0) | 0.373 | 0.58 | True | 4.1/9.3 | 2.0/4.8 | 0.212/0.21 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x3.375, std x0.614 (body err 0.073 m) |
| 14 | 81.2 | 480.89 | model_12000.pt | 9.61 | 364.9 (366.5) | 0.344 | 0.56 | True | 2.9/6.4 | 2.1/5.2 | 0.207/0.207 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x4.0, std x0.522 (body err 0.0638 m); (suggestion) not quiet after landing (arm 0.803 rad/s, torso 0.399 rad/s, action change 0.0527) -> quiet x1.5 |
| 15 | 92.1 | 448.13 | model_13499.pt | 9.489 | 367.5 (370.1) | 0.392 | 0.58 | True | 6.4/11.2 | 2.7/6.7 | 0.229/0.2 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x4.0, std x0.522 (body err 0.0698 m); (suggestion) not quiet after landing (arm 1.086 rad/s, torso 0.686 rad/s, action change 0.1854) -> quiet x1.5 |
| 16 | 101.0 | 455.34 | model_14998.pt | 9.576 | 363.1 (366.5) | 0.438 | 0.6 | True | 3.5/5.8 | 2.0/6.6 | 0.214/0.18 | (suggestion) full flip landed -> keep knobs, train on; (suggestion) took off 5 steps early -> stay-down x1.5; (suggestion) flow complete -> fidelity stage 1: tracking x4.0, std x0.522 (body err 0.0699 m); (suggestion) not quiet after landing (arm 0.47 rad/s, torso 0.412 rad/s, action change 0.0723) -> quiet x1.5 |

## LLM decision applied to round 16

reasoning: 

- priority: P1 delay-buffer reset bug (0 rad targets after every reset) - fixed in code
- priority: P2 quietness after landing (action change 0.185, pelvis 0.27 m/s): expected to follow P1; otherwise stand terms next round
- priority: - wrists: waived (cosmetic, unreliable GVHMR hand orientation)
- code: rl/mimic_generic.py: generic (L0) layer; HoldDelayedActuator fixes the 0-rad targets after reset
- code: rl/flip_rewards.py: generic part replaced by imports from mimic_generic (names unchanged)
- code: library v2: scopes generic / family:aerial / task:backflip_3, lessons, mark_verified, promote, freeze; migrated
- code: stop_criteria.json/.py + quant_report section S + harness enforcement; critic --task

## Library changes after round 16 (RSI on the checklist)

- suggest: fix backflip_3/joint:shoulder_yaw:takeoff (severity 5.51, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:takeoff (severity 5.34, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:flight (severity 5.16, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:crouch (severity 3.94, weight now 0.0)
- suggest: fix backflip_3/body:wrist_yaw:takeoff (severity 3.85, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:stand_after (severity 3.68, weight now 0.0)
- suggest: fix backflip_3/jitter:all:settle (severity 3.44, weight now 1.0)
- suggest: fix backflip_3/jitter:hip_yaw:stand_after (severity 3.25, weight now 0.0)
- suggest: fix backflip_3/joint:elbow:takeoff (severity 3.23, weight now 0.0)
- suggest: fix backflip_3/body:wrist_yaw:flight (severity 3.17, weight now 0.0)
- suggest: fix backflip_3/body:ankle_roll:takeoff (severity 2.86, weight now 0.0)
- suggest: fix backflip_3/jitter:ankle_pitch:settle (severity 2.85, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_roll:flight (severity 2.66, weight now 0.0)
- suggest: fix backflip_3/jitter:knee:stand_after (severity 2.53, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_yaw:stand (severity 2.42, weight now 0.0)
- suggest: fix backflip_3/jitter:ankle_pitch:stand_after (severity 2.33, weight now 0.0)
- suggest: fix backflip_3/jitter:ankle_pitch:land (severity 2.28, weight now 0.0)
- suggest: fix backflip_3/body:knee:flight (severity 2.26, weight now 0.0)
- suggest: fix backflip_3/joint:elbow:crouch (severity 2.22, weight now 0.0)
- suggest: fix backflip_3/joint:ankle_pitch:takeoff (severity 2.19, weight now 0.0)
- suggest: fix backflip_3/body:knee:takeoff (severity 2.19, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_yaw:takeoff (severity 2.18, weight now 0.0)
- suggest: fix backflip_3/asymmetry:wrist_roll:flight (severity 2.17, weight now 0.0)
- suggest: fix backflip_3/joint:shoulder_yaw:flight (severity 2.15, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:stand (severity 2.01, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_yaw:stand_after (severity 1.96, weight now 0.0)
- suggest: fix backflip_3/body:ankle_roll:crouch (severity 1.92, weight now 0.0)
- suggest: fix backflip_3/asymmetry:hip_yaw:takeoff (severity 1.92, weight now 0.0)
- suggest: fix backflip_3/asymmetry:shoulder_yaw:crouch (severity 1.9, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:land (severity 1.87, weight now 0.0)
- suggest: fix backflip_3/joint:elbow:land (severity 1.8, weight now 0.0)
- suggest: fix backflip_3/jitter:hip_yaw:settle (severity 1.79, weight now 0.0)
- suggest: fix backflip_3/body:elbow:flight (severity 1.79, weight now 0.0)
- suggest: fix backflip_3/jitter:ankle_roll:stand_after (severity 1.74, weight now 0.0)
- suggest: fix backflip_3/jitter:hip_pitch:stand_after (severity 1.72, weight now 0.0)
- suggest: fix backflip_3/body:wrist_yaw:land (severity 1.6, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_pitch:settle (severity 1.58, weight now 0.0)
- suggest: fix backflip_3/joint:shoulder_pitch:flight (severity 1.54, weight now 0.0)
- suggest: fix backflip_3/jitter:waist_roll:land (severity 1.48, weight now 0.0)
- suggest: fix backflip_3/body:ankle_roll:land (severity 1.45, weight now 0.0)
- suggest: fix backflip_3/jitter:knee:settle (severity 1.39, weight now 0.0)
- suggest: fix backflip_3/body:wrist_yaw:stand (severity 1.38, weight now 0.0)
- suggest: fix backflip_3/joint:shoulder_roll:flight (severity 1.37, weight now 0.0)
- suggest: fix backflip_3/body:wrist_yaw:crouch (severity 1.35, weight now 0.0)
- suggest: fix backflip_3/joint:knee:land (severity 1.34, weight now 0.0)
- suggest: fix backflip_3/asymmetry:wrist_roll:crouch (severity 1.32, weight now 0.0)
- suggest: fix backflip_3/joint:hip_pitch:takeoff (severity 1.32, weight now 0.0)
- suggest: fix backflip_3/joint:shoulder_pitch:land (severity 1.24, weight now 0.0)
- suggest: fix backflip_3/jitter:wrist_roll:stand_after (severity 1.23, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_roll:crouch (severity 1.21, weight now 0.0)
- suggest: fix backflip_3/jitter:shoulder_yaw:stand_after (severity 1.21, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_yaw:settle (severity 1.21, weight now 0.0)
- suggest: fix backflip_3/joint:wrist_yaw:flight (severity 1.19, weight now 0.0)
- suggest: fix backflip_3/body:knee:crouch (severity 1.17, weight now 0.0)
- suggest: fix backflip_3/joint:elbow:flight (severity 1.11, weight now 0.0)
- suggest: fix backflip_3/asymmetry:shoulder_roll:crouch (severity 1.02, weight now 0.0)
- suggest: fix backflip_3/joint:shoulder_yaw:crouch (severity 1.01, weight now 0.0)
- NEW check backflip_3/joint:wrist_yaw:crouch (severity 3.17) with template fix (fix not switched on: LLM decides)
- NEW check backflip_3/joint:wrist_yaw:land (severity 2.55) with template fix (fix not switched on: LLM decides)

## Needs a hand-written fix (template cannot express it or did not help)

| check | severity | why | detail |
|---|---|---|---|
| backflip_3/body:ankle_roll:flight | 3.39 | template fix did not reduce the severity for 2 rounds | left_ankle_roll_link: mean 0.27 m, max 0.40 m |
| backflip_3/jitter:all:stand_after | 1.73 | template fix did not reduce the severity for 2 rounds | mean action change 0.086 (quiet < 0.05) |
| backflip_3/asymmetry:shoulder_yaw:stand_after | 1.19 | template fix did not reduce the severity for 2 rounds | left/right differ 17 deg vs reference 5 deg |

## Automatic critic, round 16 (top issues, severity = measured / tolerance)

| severity | kind | what | phase | detail |
|---|---|---|---|---|
| 5.51 | joint | shoulder_yaw | takeoff | left_shoulder_yaw_joint: mean |err| 83 deg (signed +83), step 97: robot +0.77 vs ref -1.04 rad |
| 5.34 | joint | wrist_pitch | takeoff | right_wrist_pitch_joint: mean |err| 80 deg (signed +80), step 92: robot +1.09 vs ref -0.33 rad |
| 5.16 | joint | wrist_pitch | flight | right_wrist_pitch_joint: mean |err| 77 deg (signed +77), step 107: robot +1.19 vs ref -0.43 rad |
| 3.94 | joint | wrist_pitch | crouch | right_wrist_pitch_joint: mean |err| 59 deg (signed +59), step 90: robot +1.12 vs ref -0.18 rad |
| 3.85 | body | wrist_yaw | takeoff | left_wrist_yaw_link: mean 0.31 m, max 0.40 m |
| 3.68 | joint | wrist_pitch | stand_after | left_wrist_pitch_joint: mean |err| 55 deg (signed -55), step 170: robot -1.20 vs ref -0.18 rad |
| 3.44 | jitter | all | settle | mean action change 0.172 (quiet < 0.05) |
| 3.39 | body | ankle_roll | flight | left_ankle_roll_link: mean 0.27 m, max 0.40 m |

best so far: {'run': '2026-10-23_10-10-11_flipauto_r14', 'ckpt': 'model_12000.pt', 'score': 9.61, 'round': 14}

knobs now: `{"flip_rewards": 2.0, "knee_limit": 120.0, "ee_threshold": 0.6, "anchor_pos_threshold": 0.4, "weights": {"flip_pushoff": 2.0, "flip_lean": 1.5, "flip_spin": 3.0, "flip_airborne": 1.5, "flip_height": 1.0, "flip_land": 3.375, "flip_plane_axis": 3.375, "flip_plane_rate": 2.25, "flip_leg_sym": 6.0, "flip_leg_track": 6.0, "flip_leg_calm": 3.0, "flip_feet_together": 6.0, "flip_tuck": 9.0, "flip_rot_track": 2.0, "flip_land_balance": 3.0, "flip_stay_down": 5.0, "flip_stand_quiet": 3.0, "flip_stand_still": 4.0}, "prior": {"stand": 0.52, "crouch": 2.6, "takeoff": 2.0, "flight": 0.3, "land": 2.197, "settle": 0.5, "other": 0.5}, "terms": {"term_flight_spread": {"max_d": 0.6}, "term_hip_extended": {"max_hip": 0.0}, "term_stand_fail": {"max_d": 0.45, "max_tilt": 25.0}, "term_leg_twist": {"max_roll": 0.6, "max_yaw": 0.8, "max_knee_sep": 0.45}}, "tracking": {"stage": 1, "scale": 3.375, "std_scale": 0.614}, "extra_dyn": [{"name": "agent_r09_hip_tuck", "func": "dyn_joint", "weight": 3.0, "params": {"joints": ["left_hip_pitch_joint", "right_hip_pitch_joint"], "phases": ["flight"], "std": 0.6}}, {"name": "agent_r09_arms_air", "func": "dyn_joint", "weight": 2.0, "params": {"joints": ["left_shoulder_pitch_joint", "right_shoulder_pitch_joint", "left_shoulder_roll_joint", "right_shoulder_roll_joint", "left_shoulder_yaw_joint", "right_shoulder_yaw_joint", "left_elbow_joint", "right_elbow_joint"], "phases": ["takeoff", "flight", "land"], "std": 0.8}}, {"name": "agent_r10_arms_stand", "func": "dyn_joint", "weight": 3.0, "params": {"joints": ["left_shoulder_pitch_joint", "right_shoulder_pitch_joint", "left_shoulder_roll_joint", "right_shoulder_roll_joint", "left_shoulder_yaw_joint", "right_shoulder_yaw_joint", "left_elbow_joint", "right_elbow_joint"], "phases": ["settle", "stand_after"], "std": 1.0}}, {"name": "agent_r11_legs_stand", "func": "dyn_joint", "weight": 3.0, "params": {"joints": ["left_knee_joint", "right_knee_joint", "left_hip_pitch_joint", "right_hip_pitch_joint", "left_ankle_pitch_joint", "right_ankle_pitch_joint"], "phases": ["stand_after"], "std": 0.4}}, {"name": "agent_r13_arms_prestand", "func": "dyn_joint", "weight": 2.0, "params": {"joints": ["left_shoulder_pitch_joint", "right_shoulder_pitch_joint", "left_shoulder_roll_joint", "right_shoulder_roll_joint", "left_shoulder_yaw_joint", "right_shoulder_yaw_joint", "left_elbow_joint", "right_elbow_joint"], "phases": ["stand"], "std": 0.8}}], "delay_ms": 25.0}`
