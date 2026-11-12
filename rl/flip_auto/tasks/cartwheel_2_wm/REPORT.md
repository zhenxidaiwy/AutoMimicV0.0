# Backflip auto harness (G1 EDU limits: knee 120 N.m)

| round | train min | ep len | best ckpt | score | rotation deg (max) | pelvis rise m | airborne s | landed | out-of-plane deg (mean/max) | legs asym/err deg | feet dist max/touchdown m | adjustment |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 60.6 | 66.44 | model_1809.pt | 2.0 | 261.7 (264.9) | 0.014 | 0.12 | False | None/None | None/None | None/None | (suggestion) no jump -> pushoff x1.5, takeoff prior x1.3, crouch x1.2 |
| 2 | 60.6 | 4.62 | model_531.pt | nan | 472.8 (616.0) | 5.615 | 0.38 | False | None/None | None/None | None/None | (suggestion) rotates but does not land -> land x1.5, land prior x1.3; (suggestion) not standing stably (feet end nan m) -> stand limits 0.765 m / 35.0 deg |
| 3 | 60.6 | 39.14 | model_1812.pt | 1.537 | 196.4 (200.0) | 0.016 | 0.26 | False | None/None | None/None | None/None | (suggestion) suspicious airborne without rise -> airborne weight / 2 |
| 4 | 50.8 | 28.46 | model_2294.pt | 1.112 | 142.0 (144.4) | 0.004 | 0.24 | False | None/None | None/None | None/None | (suggestion) suspicious airborne without rise -> airborne weight / 2 |
| 5 | 1.5 | None | None | None | None (None) | None | None | None | None/None | None/None | None/None |  |

## LLM decision applied to round 5

reasoning: 

- priority: P1 keep the r04 reference / priors (the hands-on-floor entry appeared)
- priority: P2 more training time on the support phase: warm start from the last r04 checkpoint, full 60 min
- priority: watch: GPU faults (CUDA 999), guard counters, support-phase probe (starts 46 / 60)
- code: rl/flip_auto/harness.py: segment probe called with TASK (was CLIP: probed the PPO run for cartwheel_2_wm)
- code: rl/flip_auto/quant_report.py: reads segments_<TASK>_*.json

best so far: {'run': '2026-11-04_16-17-39_cw2wm_r01', 'ckpt': 'model_1809.pt', 'score': 2.0, 'round': 1}

knobs now: `{"flip_rewards": 2.0, "knee_limit": 120.0, "ee_threshold": 0.6, "anchor_pos_threshold": 0.4, "weights": {"flip_pushoff": 2.0, "flip_lean": 1.0, "flip_spin": 3.0, "flip_airborne": 1.5, "flip_height": 1.0, "flip_land": 1.0, "flip_plane_axis": 1.5, "flip_plane_rate": 1.0, "flip_leg_sym": 0.0, "flip_leg_track": 1.0, "flip_leg_calm": 0.5, "flip_feet_together": 2.0, "flip_tuck": 2.0, "flip_rot_track": 2.0, "flip_land_balance": 0.0, "flip_stay_down": 1.0, "flip_stand_quiet": 3.0, "flip_stand_still": 3.0}, "tracking": {"stage": 0, "scale": 1.0, "std_scale": 1.0}, "terms": {"term_flight_spread": null, "term_hip_extended": {"max_hip": 1.2}, "term_stand_fail": {"max_d": 0.85, "max_tilt": 40.0, "max_waist": 0.6}, "term_leg_twist": null}, "prior": {"stand": 0.4, "crouch": 2.0, "takeoff": 2.0, "flight": 0.3, "land": 1.0, "settle": 0.5, "other": 0.5, "lunge": 3.0, "support": 2.0}, "hand_friction": 0.6, "delay_ms": 25.0, "extra_dyn": [], "reference": {"variant": "reachqp_vlm_hold", "labels": "labels_hold_50fps.npz"}}`
