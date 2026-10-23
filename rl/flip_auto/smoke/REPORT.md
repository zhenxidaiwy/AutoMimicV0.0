# Backflip auto harness (G1 EDU limits: knee 120 N.m)

| round | train min | ep len | best ckpt | score | rotation deg (max) | pelvis rise m | airborne s | landed | adjustment |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 1.3 | 14.73 | model_0.pt | 1.276 | 95.0 (96.5) | 0.045 | 0.12 | False | fell before take-off -> lean x1.5, stand/crouch prior x1.3 |
| 2 | 1.4 | 16.82 | model_19.pt | 1.288 | 96.5 (98.5) | 0.011 | 0.2 | False | fell before take-off -> lean x1.5, stand/crouch prior x1.3 |

best so far: {'run': '2026-10-22_17-16-24_flipauto_r02', 'ckpt': 'model_19.pt', 'score': 1.288, 'round': 2}

knobs now: `{"flip_rewards": 2.0, "knee_limit": 120.0, "ee_threshold": 0.6, "anchor_pos_threshold": 0.4, "weights": {"flip_pushoff": 2.0, "flip_lean": 2.25, "flip_spin": 3.0, "flip_airborne": 1.5, "flip_height": 1.0, "flip_land": 1.0}, "prior": {"stand": 0.676, "crouch": 3.38, "takeoff": 2.0, "flight": 0.3, "land": 1.0, "settle": 0.5, "other": 0.5}}`
