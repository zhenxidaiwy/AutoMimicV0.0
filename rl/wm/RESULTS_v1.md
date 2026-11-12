# World model v1: P1 data + P2 fit (2026-11-02)

## P1 data (`collect_all.py`)

- 61 checkpoints, all collected: backflip 16, cartwheel 16, getup 14, multi_train_v1 6, gouxiong 4,
  shanshenbu 3, multi_canon_v1 2.
- 512 envs x 200 steps per checkpoint gives 6.25 M transitions (2.6 GB in `~/projects/dance/wm_data/v1`).
  Collection took 18.8 min.
- Resets per env per 200 steps: backflip 4.5, cartwheel 1.1, getup 0.0, gouxiong 6.6. These are clip ends and
  falls. Windows never cross a reset.
- Fixed before the full run, found in the tiny test:
  - After `reset()`, every env reported done at step 0, so the stale pre-reset state was recorded. Fix: one
    warm-up step.
  - The default z-only tracking terminations (0.25 m) cut cartwheel sequences. Raised to 0.6 m, the same value as
    the hand-support training; the thresholds are recorded in `xi.terminations`.
- Consistency check: |root dp - v dt| / |dp| = 5-9 %; joints 14-23 % (4 physics substeps per control step).

## P2 fit (`fit.py`, MLP 3 x 1024, k = 8, 50 k iterations, batch 2048, 33 min on the RTX 5060 laptop)

- Held out (not trained on): cartwheel_2 r11 model_12000, cartwheel_2 r08 model_10493, backflip r15
  model_13499, getup r09_part1 model_24100.
- 57 training files; 4.97 M training windows.
- Open loop on logged actions. Each cell is the error at the last step, mean / p90 over windows.

| set | H | windows | root height (m) | joint pos (rad) | tilt (deg) | tracked bodies (m) | root xy (m) |
|---|---|---|---|---|---|---|---|
| held out | 8 | 20000 | 0.015 / 0.034 | 0.044 / 0.085 | 4.0 / 8.1 | 0.025 / 0.047 | 0.027 / 0.046 |
| held out | 32 | 20000 | **0.033** / 0.071 | **0.064** / 0.117 | 9.1 / 16.1 | **0.045** / 0.077 | 0.140 / 0.271 |
| held-out cartwheel, support (frames 46-80) | 8 | 6602 | 0.031 / 0.064 | 0.079 / 0.113 | 8.5 / 14.5 | 0.041 / 0.061 | 0.033 / 0.058 |
| held-out cartwheel, support (frames 46-80) | 32 | 6602 | **0.041** / 0.087 | **0.063** / 0.092 | 10.2 / 18.4 | **0.049** / 0.082 | 0.153 / 0.281 |
| training sample (backflip r01, early) | 32 | 9459 | 0.101 / 0.222 | 0.144 / 0.259 | 39.0 / 75.8 | 0.094 / 0.172 | 0.344 / 0.680 |

**P2 gate:** 32 steps, root height < 5 cm, joints < 0.1 rad, tracked bodies < 8 cm, including hand support.
It **passes on the mean** in every held-out set, including the support phase (4.1 cm / 0.063 rad / 4.9 cm).
At p90 it does not pass:

- support phase: height 8.7 cm, bodies 8.2 cm;
- all held out: joints 0.117 rad.

Not in the gate but weak:

- tilt after 32 steps: 9-10 deg mean, 16-18 deg p90;
- root xy drift: 14-15 cm mean;
- the early backflip policies (falls, chaotic motion): about 3x the held-out errors.

The training loss is noisy (root term 0.25-0.82 between logs). Next lever if needed: 3 x 2048, or more data from
falling policies.

## v1b: clip-end teleports removed (branch `wm-speedup`, 2026-11-02)

At the clip end, mjlab's motion command resamples a start frame and teleports the robot **without** `done`. This
affected 0.5-1 % of the v1 tracking transitions; the torch FK check found it. `wm.Sequences` now treats a frame
jump as a reset. Columns are H32 mean / p90.

| model | set | height (m) | joints (rad) | tilt (deg) | bodies (m) | root xy (m) |
|---|---|---|---|---|---|---|
| v1 | held out, old windows | 0.033 / 0.071 | 0.064 / 0.117 | 9.1 / 16.1 | 0.045 / 0.077 | 0.140 / 0.271 |
| v1 | held out, clean windows | 0.030 / 0.065 | 0.059 / 0.105 | 8.1 / 15.0 | 0.043 / 0.069 | 0.102 / 0.194 |
| **v1b** | held out | **0.024** / 0.062 | **0.054** / 0.106 | 8.4 / 18.1 | **0.042** / 0.074 | **0.078** / 0.167 |
| **v1b** | cartwheel support | **0.029** / 0.065 | 0.061 / 0.087 | **7.8** / 14.9 | 0.050 / 0.080 | 0.122 / 0.218 |

### Is the model data-limited?

**D1: training-set checkpoints of the same skills vs held out.** The training-set checkpoints are neighbours of the
held-out ones (cartwheel r10 / r09, backflip r13, getup r09 model_23500).

- On training-set checkpoints the errors are only 15-25 % lower: joints 0.044 vs 0.054 rad, bodies 0.034 vs
  0.042 m, height 2.0 vs 2.4 cm.
- So the generalisation gap is small, and most of the error is there even on training data: under-fitting or
  noise the model cannot see.

**D2: half of the env trajectories of every file**, same 50 k iterations.

- Held-out errors are practically unchanged: height 2.5 vs 2.4 cm, joints 0.053 vs 0.054 rad, bodies 0.040 vs
  0.042 m, support 0.029 / 0.061 / 0.053.
- Doubling the data did not help.

**Verdict: not data-quantity-limited.** Next levers, in order:

1. Make the per-env actuator lag (mjlab `delay_max_lag` 0-5 physics steps, random per env) an input; today it is
   noise the deterministic model cannot see.
2. Capacity / longer fit (3 x 2048).
3. Targeted coverage (backflip flight, falls) rather than more of the same.

## Comparison (scratchpad `wm_compare.py`, 32-step open loop, mean error at step 32)

Baselines on the same windows:

- **persistence:** s' = s;
- **constant velocity:** joints and root keep their current velocity.

The tracked-body column uses the model's body head on each baseline's states.

| held-out set | predictor | height (m) | joints (rad) | tilt (deg) | bodies (m) | root xy (m) |
|---|---|---|---|---|---|---|
| cartwheel support 46-80 (6602) | **world model** | **0.041** | **0.063** | **10.2** | **0.049** | **0.153** |
| | persistence | 0.050 | 0.410 | 146.1 | 0.238 | 0.531 |
| | constant velocity | 0.291 | 1.797 | 146.1 | 0.652 | 0.642 |
| cartwheel all phases (10k) | world model | 0.019 | **0.040** | **5.4** | **0.036** | **0.086** |
| | persistence | **0.012** | 0.093 | 15.1 | 0.048 | 0.103 |
| backflip r15 (10k) | **world model** | **0.058** | **0.103** | **13.3** | **0.064** | **0.286** |
| | persistence | 0.120 | 0.360 | 41.0 | 0.147 | 0.305 |
| getup r09 (10k) | **world model** | **0.041** | **0.079** | **12.2** | **0.049** | 0.104 |
| | persistence | 0.068 | 0.205 | 19.0 | 0.082 | 0.103 |

Constant velocity is worse than persistence everywhere. Its rows are left out except for the support phase.

Where the model gains:

- **Dynamic phases:** in cartwheel support, joints are 6.5x better than persistence, bodies 4.8x, tilt 14x.
- **Near-still windows:** it loses only on height in the cartwheel set, which is mostly the 7.5 s hold
  (1.9 vs 1.2 cm). It is also no better than persistence on getup root xy.

**Backflip r15 fails the P2 gate on the mean:**

- height 5.8 cm (gate 5 cm);
- joints 0.103 rad (gate 0.1 rad).

Flight + landing is the weakest skill.

**Speed:** 4096 imagined rollouts x 32 steps run at 1.59 M steps/s on the RTX 5060 Laptop. The model has 2.6 M
parameters. For reference, P1 collection in mjlab ran at about 5.5 k steps/s, but that includes policy inference
and logging, so it is not a like-for-like simulator benchmark.
