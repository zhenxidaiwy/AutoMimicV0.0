# Round 2 (world-model trainer) - analysis (step 2)

**One-line verdict:** invalid round - the trainer went NaN at minute 17, so every exported policy outputs NaN; the
robot is flung off the floor at step ~3 and the simulation blows up (empty frames from step 61).

## Video (r02_model_531, all 13 sheets 000-487 reviewed)

| steps | what the robot does |
|---|---|
| 0-2 | standing, starts to move |
| 3-16 | thrown up and sideways, flails |
| 17-33 | tumbling in the air away from the reference |
| 34-60 | far away / above the floor, limbs at random angles |
| 61-487 | empty frames: the state is NaN, nothing is rendered |

The quant report agrees: joints up to 27,747 rad, pelvis 8.5 m up, most metrics nan, and all three checkpoints score
nan.

## Cause (train_cw2wm_r02.log)

- **Before the failure (it 20-420) the run was healthy:** wm_loss 0.10-0.36, grad_norm < 0.7, head MSE 21-37.
- **Failure:** at it 440 (min 17.2), wm_loss, grad_norm, rew_step, critic_loss and both head losses all became NaN in
  the same log interval. They never recovered, and the episode length dropped 12.8 -> 4.6.
- **Probable route:**
  - The real physics produced a non-finite or very large state; MuJoCo had already reported `nefc overflow`.
  - The replay ring stores states in fp16 (max 65504), and none of the optimizers checks for non-finite steps.
  - One bad batch therefore poisoned the model, the heads, the critic and the policy.
  - The guard counters added for r03 will show which part actually triggered it.
- **This is a defect of the inner trainer, not of the knobs.** PPO r02 ran the same knobs without a NaN.

## Fix (code, trainer only; env, rewards and knobs unchanged)

rl/wm/speedup/online.py:

- Collected states that are non-finite or outside the fp16 range are zeroed and marked done/invalid. They are excluded
  from model windows, head targets and imagined starts.
- Non-finite observations are kept out of the policy normaliser.
- Actions go through nan_to_num.
- The world-model and heads optimizers skip a step whose loss or grad norm is non-finite.

rl/wm/speedup/shac_paper.py:

- Diverged imagined rollouts are dropped from the actor loss.
- The actor and critic skip non-finite steps, and the critic targets are filtered.

All guards are counted in the train log (`bad_state`, `skip_*`, `nonfinite_rollouts`).

## -> r03

- r03 uses the r02 knobs unchanged, from scratch, with the fixed trainer.
- Round 2 stays in the history as "invalid (trainer NaN)". It is not deleted.
