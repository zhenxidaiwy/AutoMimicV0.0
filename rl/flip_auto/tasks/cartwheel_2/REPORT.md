# Backflip auto harness (G1 EDU limits: knee 120 N.m)

| round | train min | ep len | best ckpt | score | rotation deg (max) | pelvis rise m | airborne s | landed | out-of-plane deg (mean/max) | legs asym/err deg | feet dist max/touchdown m | adjustment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 95.5 | 145.97 | model_1000.pt | 1.93 | 231.0 (236.0) | 0.007 | 0.12 | False | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 2 | 93.7 | 179.26 | model_1000.pt | 1.82 | 232.5 (234.1) | 0.063 | 0.08 | False | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 3 | 94.8 | 477.54 | model_2998.pt | 5.642 | 254.5 (255.7) | 0.014 | 0.24 | True | None/None | None/None | None/None | (suggestion) suspicious airborne without rise -> airborne weight / 2 |
| 4 | 94.6 | 478.11 | model_3500.pt | 5.704 | 259.1 (259.1) | 0.053 | 0.22 | True | None/None | None/None | None/None | (suggestion) full flip landed -> keep knobs, train on |
| 5 | 95.4 | 473.49 | model_5500.pt | 5.767 | 259.0 (259.1) | 0.049 | 0.24 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 6 | 96.4 | 437.57 | model_7000.pt | 5.72 | 252.5 (253.1) | 0.043 | 0.2 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 7 | 97.9 | 473.9 | model_8500.pt | 5.842 | 261.0 (261.1) | 0.05 | 0.22 | True | None/None | None/None | None/None | (suggestion) full flip landed -> keep knobs, train on |
| 8 | 97.7 | 449.96 | model_10493.pt | 5.84 | 264.3 (265.7) | 0.027 | 0.2 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 9 | 93.0 | 419.62 | model_11992.pt | 5.753 | 263.2 (264.9) | 0.039 | 0.22 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 10 | 94.2 | 449.5 | model_13491.pt | 5.793 | 261.7 (261.9) | 0.046 | 0.2 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 11 | 95.7 | 432.38 | model_12500.pt | 5.776 | 291.4 (294.2) | 0.073 | 0.2 | True | None/None | None/None | None/None | (suggestion) full flip landed -> keep knobs, train on |
| 12 | 97.6 | 451.55 | model_13500.pt | 5.808 | 256.0 (257.9) | 0.052 | 0.2 | True | None/None | None/None | None/None | (suggestion) full flip landed -> keep knobs, train on |
| 13 | 97.0 | 454.63 | model_13999.pt | 5.823 | 261.2 (263.4) | 0.012 | 0.2 | True | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |

## LLM decision applied to round 13

reasoning: 

- priority: rollback to r11 model_12500 with r11's library weights
- priority: single change: jitter:all:settle weight 1 (it lowered settle jitter 3.38 -> 2.2 in r12)
- priority: waive the two support asymmetry checks (reviewed one by one, r12_llm.md)
- knob extra_dyn: [{'name': 'agent_r05_base_still', 'func': 'dyn_base_still', 'weight': 3.0, 'params': {'phases': ['stand_after'], 'std_v': 0.1, 'std_w': 0.3}}, {'name': 'agent_r08_hold_spot', 'func': 'dyn_hold_spot', 'weight': 4.0, 'params': {'phases': ['stand_after'], 'std': 0.1}}]
- library asymmetry:wrist_roll:support: weight 0.0
- library asymmetry:hip_yaw:support: weight 0.0
- library jitter:wrist_roll:land: weight 1.0
- library jitter:all:settle: weight 1.0

## Library changes after round 13 (RSI on the checklist)

- suggest: fix cartwheel_2/asymmetry:wrist_roll:stand (severity 4.31, weight now 0.0)
- suggest: fix cartwheel_2/body:ankle_roll:land (severity 4.16, weight now 0.0)
- suggest: fix cartwheel_2/jitter:all:settle (severity 3.32, weight now 1.0)
- suggest: fix cartwheel_2/body:knee:land (severity 3.06, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:shoulder_yaw:stand (severity 2.98, weight now 0.0)
- suggest: fix cartwheel_2/contact:right_foot:land (severity 2.67, weight now 0.0)
- suggest: fix cartwheel_2/jitter:wrist_roll:stand (severity 2.64, weight now 0.0)
- suggest: fix cartwheel_2/jitter:ankle_roll:land (severity 2.62, weight now 0.0)
- suggest: fix cartwheel_2/joint:ankle_pitch:land (severity 2.59, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:shoulder_yaw:lunge (severity 2.57, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:wrist_roll:lunge (severity 2.53, weight now 0.0)
- suggest: fix cartwheel_2/body:ankle_roll:support (severity 2.04, weight now 0.0)
- suggest: fix cartwheel_2/body:ankle_roll:settle (severity 1.98, weight now 0.0)
- suggest: fix cartwheel_2/joint:hip_pitch:land (severity 1.98, weight now 0.0)
- suggest: fix cartwheel_2/joint:wrist_roll:support (severity 1.97, weight now 0.0)
- suggest: fix cartwheel_2/jitter:shoulder_yaw:land (severity 1.88, weight now 0.0)
- suggest: fix cartwheel_2/jitter:wrist_roll:lunge (severity 1.87, weight now 0.0)
- suggest: fix cartwheel_2/body:wrist_yaw:support (severity 1.77, weight now 0.0)
- suggest: fix cartwheel_2/body:wrist_yaw:lunge (severity 1.76, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:shoulder_yaw:land (severity 1.71, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:wrist_roll:settle (severity 1.67, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:wrist_roll:support (severity 1.67, weight now 0.0)
- suggest: fix cartwheel_2/body:ankle_roll:lunge (severity 1.55, weight now 0.0)
- suggest: fix cartwheel_2/joint:knee:stand (severity 1.53, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:hip_yaw:support (severity 1.48, weight now 0.0)
- suggest: fix cartwheel_2/body:wrist_yaw:settle (severity 1.34, weight now 0.0)
- suggest: fix cartwheel_2/joint:wrist_roll:lunge (severity 1.31, weight now 0.0)
- suggest: fix cartwheel_2/joint:hip_roll:support (severity 1.28, weight now 0.0)
- suggest: fix cartwheel_2/body:wrist_yaw:land (severity 1.28, weight now 0.0)
- suggest: fix cartwheel_2/joint:ankle_pitch:stand (severity 1.26, weight now 0.0)
- suggest: fix cartwheel_2/body:elbow:support (severity 1.25, weight now 0.0)
- suggest: fix cartwheel_2/body:knee:support (severity 1.22, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:hip_pitch:support (severity 1.22, weight now 0.0)
- suggest: fix cartwheel_2/asymmetry:shoulder_yaw:support (severity 1.18, weight now 0.0)
- suggest: fix cartwheel_2/joint:wrist_yaw:land (severity 1.17, weight now 0.0)
- suggest: fix cartwheel_2/joint:hip_yaw:support (severity 1.15, weight now 0.0)
- suggest: fix cartwheel_2/body:ankle_roll:stand_after (severity 1.14, weight now 0.0)
- suggest: fix cartwheel_2/body:knee:lunge (severity 1.13, weight now 0.0)
- suggest: fix cartwheel_2/joint:shoulder_yaw:support (severity 1.12, weight now 0.0)
- suggest: fix cartwheel_2/joint:shoulder_pitch:land (severity 1.12, weight now 0.0)
- suggest: fix cartwheel_2/jitter:shoulder_yaw:stand (severity 1.11, weight now 0.0)
- suggest: fix cartwheel_2/joint:knee:support (severity 1.1, weight now 0.0)
- suggest: fix cartwheel_2/joint:hip_pitch:support (severity 1.05, weight now 0.0)
- suggest: fix cartwheel_2/joint:elbow:support (severity 1.02, weight now 0.0)

## Needs a hand-written fix (template cannot express it or did not help)

| check | severity | why | detail |
|---|---|---|---|
| cartwheel_2/jitter:wrist_roll:land | 3.14 | template fix did not reduce the severity for 2 rounds | left_wrist_roll_joint: joint acceleration RMS 54 vs reference 1 rad/s^2 |

## Automatic critic, round 13 (top issues, severity = measured / tolerance)

| severity | kind | what | phase | detail |
|---|---|---|---|---|
| 4.31 | asymmetry | wrist_roll | stand | left/right differ 44 deg vs reference 1 deg |
| 4.16 | body | ankle_roll | land | left_ankle_roll_link: mean 0.33 m, max 0.46 m |
| 3.32 | jitter | all | settle | mean action change 0.166 (quiet < 0.05) |
| 3.14 | jitter | wrist_roll | land | left_wrist_roll_joint: joint acceleration RMS 54 vs reference 1 rad/s^2 |
| 3.06 | body | knee | land | left_knee_link: mean 0.24 m, max 0.31 m |
| 2.98 | asymmetry | shoulder_yaw | stand | left/right differ 31 deg vs reference 1 deg |
| 2.67 | contact | right_foot | land | right_foot off the floor for 8 of 14 steps the reference has it down |
| 2.64 | jitter | wrist_roll | stand | right_wrist_roll_joint: joint acceleration RMS 46 vs reference 1 rad/s^2 |

best so far: {'run': '2026-10-26_08-05-57_cw2auto_r07', 'ckpt': 'model_8500.pt', 'score': 5.842, 'round': 7}

knobs now: `{"flip_rewards": 2.0, "knee_limit": 120.0, "ee_threshold": 0.6, "anchor_pos_threshold": 0.4, "weights": {"flip_pushoff": 2.0, "flip_lean": 1.0, "flip_spin": 3.0, "flip_airborne": 1.5, "flip_height": 1.0, "flip_land": 1.0, "flip_plane_axis": 1.5, "flip_plane_rate": 1.0, "flip_leg_sym": 0.0, "flip_leg_track": 1.0, "flip_leg_calm": 0.5, "flip_feet_together": 2.0, "flip_tuck": 2.0, "flip_rot_track": 2.0, "flip_land_balance": 0.0, "flip_stay_down": 1.0, "flip_stand_quiet": 3.0, "flip_stand_still": 3.0}, "tracking": {"stage": 0, "scale": 1.0, "std_scale": 1.0}, "terms": {"term_flight_spread": null, "term_hip_extended": {"max_hip": 1.2}, "term_stand_fail": {"max_d": 0.85, "max_tilt": 40.0, "max_waist": 0.6}, "term_leg_twist": null, "term_below_reference": {"margin": 0.12, "min_clear": 0.05}, "term_foot_lifted": {"phases": ["stand"], "max_lift": 0.05, "planted_z": 0.06}}, "prior": {"stand": 0.4, "crouch": 2.0, "takeoff": 2.0, "flight": 0.3, "land": 1.0, "settle": 0.5, "other": 0.5, "lunge": 3.0, "support": 2.0}, "hand_friction": 0.6, "delay_ms": 40.0, "extra_dyn": [{"name": "agent_r05_base_still", "func": "dyn_base_still", "weight": 3.0, "params": {"phases": ["stand_after"], "std_v": 0.1, "std_w": 0.3}}, {"name": "agent_r08_hold_spot", "func": "dyn_hold_spot", "weight": 4.0, "params": {"phases": ["stand_after"], "std": 0.1}}], "reference": {"variant": "reachqp_vlm_hold8", "labels": "labels_hold8_50fps.npz"}}`
