# Round 1 (world-model trainer) - analysis (step 2)

**One-line verdict:** the robot reaches the hand support, but it does not go over. It slides sideways on its knees,
falls, and lies on the floor with jittery limbs until the end of the clip.

## Video (r01_model_1809, all 13 sheets 000-487 reviewed frame by frame)

After step 80:

| steps | what the robot does |
|---|---|
| 80-103 | lies on its side, legs kicking |
| 104-199 | lies on its back, small limb jerks |
| 200-487 | lies prone, one leg lifting and dropping; never tries to get up |

Before step 80:

- **Steps 0-43:** the lunge roughly follows the reference.
- **Steps 44-55:** the reference goes into the handstand with its legs rising. The robot stays crouched and plants one
  hand far out.
- **Steps 56-71:** the robot slides sideways on its knees. The legs never rise.
- **Steps 72-79:** the robot tips over. One leg kicks up while it falls. This is where the 262 deg rotation comes from:
  it rolls over, it does not cartwheel.
- **Steps 80 to the end:** the robot lies on the floor. Post-clip action change is 0.64 (quiet < 0.05). Joint
  accelerations are 100x the reference, e.g. wrist roll 462 vs 4 rad/s^2.

## Quantitative (r01_quant.md)

| metric | value |
|---|---|
| landed_upright | False |
| post_fell | True |
| robustness | 0 / 5 scenarios |
| critic worst | 17.9 (wrist yaw, stand_after) |

**Training signal** (train_cw2wm_r01.log):

| metric | start | end |
|---|---|---|
| mean episode length | 12.8 | ~70 |
| falls per step | 0.073 | 0.015 |
| reward-residual head MSE | 28 | 2.3 |
| termination head BCE | 0.19 | 0.046 |

- The learned heads track the harness terms.

## Comparison with the PPO run's r01 (same knobs, cartwheel_2 r01)

- Same failure: "fell sideways at step 48 instead of going over, lay on the floor".
- Episode length at matched time: WM ~70 vs PPO 144 at ~55 min, so the WM trainer survives about half as long.
- One difference in the WM run's favour: PPO r01 still had the two terminations that fire on the reference.

## Framework gap found and fixed

- quant_report F read 0 reward terms: online.py did not print rsl_rl's `Episode_Reward/<term>:` lines.
- It now prints them as the mean real step reward x dt per term. The terms were in the env all along: the train log
  shows the `[train_dance]` setup lines.

## Diagnosis -> r02

- The causes are the reference / reward ones the PPO run found after its r01:
  - the reference g1_lock_vlm_hold does not plant both feet in the still stances (fixed by feet_plant ->
    plant_vlm_hold);
  - flip_leg_sym and flip_land_balance pay the reference itself little (0.04 / 0.62).
- They are properties of the reference and reward, not of the inner trainer, so r02 applies the same fixes and
  restarts from scratch (reward set changed), as PPO r02 did.
- The WM-specific jitter is watched, not treated, in r02. If it persists with the fixed reference, r03 raises the
  action-rate weight or switches on the library's quiet fixes.
