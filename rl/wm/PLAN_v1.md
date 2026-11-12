# World model for AutoMimic (plan v1, 2026-11-02)

Source idea: SuperMimic (Liao et al., CoRL 2026, arXiv 2610.28480), read in full (19 pages incl. appendix).
We take the idea, not the system: we do not reproduce their 129k-motion generalist tracker.

## What SuperMimic shows (the parts we use)

1. **One deterministic, differentiable dynamics model** `s' = f(s, a, xi)` fit to logged simulator transitions
   (MuJoCo Warp, 50 Hz). `xi` = the known per-episode sim context (friction, joint offsets, torso CoM). Randomness
   with a known source is an input, not something the model has to guess.
2. **The dynamics do not depend on the policy that collected them.** Transitions from earlier policies stay valid.
3. **k-step autoregressive fit** (k = 8): the model is rolled forward on logged actions and trained on its own
   errors. Loss = state + reward + noise-free observation + termination (BCE). It then stays stable over 32-step
   imagined rollouts, and longer.
4. **Policy update = BPTT through H = 32 imagined steps plus a critic beyond H** (SHAC-style, survival weight from
   the predicted termination probability). Without the critic, training fails at H <= 16, and the policy does not
   recover from pushes.
5. Numbers: the dynamics network is an MLP (2048, 2048, 2048). Batches are 10 x 2048 windows; 4096 imagined
   rollouts per update; action noise N(0, 0.1^2) during data collection. On LAFAN1, return 0.82 is reached in
   1.2 h on one GPU, while PPO in the simulator on 8 GPUs does not reach it in 18 h. Rollouts are > 10x faster
   than MuJoCo Warp. First-order gradients need about 64x fewer imagined steps than PPO on the same model.
6. Root-velocity pushes are left out: they are state discontinuities the deterministic model cannot capture.

## What it can do for AutoMimic

Our loop is: video -> reference -> per-skill PPO rounds of about 1.7 GPU-h, with an LLM deciding each round from
diagnostics. One G1 world model shared across all our skills fits the paper direction (a growing library). The
library keeps a growing *dynamics* asset as well as a growing diagnostic one.

| use | what it buys | validation |
|---|---|---|
| U1 imagined pre-screen of a decision | Before spending 1.7 GPU-h, fine-tune the current policy for a few minutes in the model with each candidate knob set, then score the predicted gates. This would have flagged r10's posture term (tilt did not move) | Retrospective: rank the real r02-r11 decisions; compare with their measured outcomes |
| U2 BPTT fine-tune rounds | A round in minutes instead of 1.7 h on the laptop GPU | Real-sim eval of the fine-tuned checkpoint with the unchanged harness metrics |
| U3 feasibility probe of a reference | Optimise an open-loop action sequence through the model to track the reference. Frames that stay infeasible (e.g. cartwheel_2 r02: palms 6-25 cm high, 2 g root drop) become a new diagnostic for physics reference repair | Compare the flagged frames with the repairs we found by hand |
| U4 pushes in imagination | Our own extension: inject a push as an edit of the root velocity in the imagined state; the dynamics model never has to fit the discontinuity | Robustness eval in the real sim |

## Data: no extra training needed

68 runs exist (backflip r01-r17, cartwheel_2 r01-r11, dance, multi-clip), including failed ones. Falls and lying on
the floor are valuable coverage. `collect.py` rolls a checkpoint out with action noise 0.1, per-env delay 0-2
steps, and fixed known friction / kp scale per run. It logs root state, joint state, tracked body poses, the
executed action and the reference frame. At about 400 B per transition (fp16), 5 M transitions is about 2 GB
(885 GB free).

## Model (sized for an RTX 5060 Laptop, 8 GB)

- State `s`:
  - root height, root orientation (in the heading frame), root linear and angular velocity (in the body frame);
  - joint position and velocity (29 + 29);
  - the last 2 executed actions, to model the delay.
  - Translation- and yaw-invariant, like the observation.
- Context `xi`: foot friction, hand friction, kp scale, delay steps, knee limit.
- Heads:
  - delta state;
  - tracked body poses in the root frame, so the tracking reward is analytic on predictions;
  - foot / hand contact probabilities, which our diagnostics already reason about;
  - termination probability.
- MLP 3 x 1024 first (about 3.5 M parameters), then 3 x 2048 if under-fit. k = 8 windows, Adam 2e-4, grad clip 1.0.
- Estimate: under 0.2 s per batch of 2048 windows on the laptop GPU, so 50 k updates in about 3 h.

## Phases and go / no-go gates

| phase | work | GPU | gate |
|---|---|---|---|
| P0 | this plan, `collect.py`, dataset manifest | none | - |
| P1 | collect from about 30 checkpoints of 3 or more skills | about 2 h | >= 2 M transitions; cartwheel support / land phases covered |
| P2 | fit the model | about 3 h | On held-out checkpoints, 32-step open-loop rollout: root height error < 5 cm, joint error < 0.1 rad, tracked-body error < 8 cm, including the hand-support phase. If not met: stop, and report why |
| P3 | U1 retrospective ranking of r02-r11 | under 1 h | The predicted direction of change of tracking / hold tilt matches the real one in >= 7 of 10 rounds |
| P4 | U2 BPTT fine-tune from cartwheel_2 best | about 2 h | Real-sim tracking and hold gates no worse than PPO, at <= 1/3 of the GPU time |

GPU work starts only after cartwheel_2 has converged; the laptop GPU (8 GB) cannot share with a training run.

## Risks

- **Hand contacts** in support phases are the hardest part to model (hybrid dynamics). SuperMimic does fit side
  rolls and flips, but with far more data.
- **Delay** makes the state non-Markov unless the action history is in the state (done above).
- **Model exploitation** in U1 / U2: the policy may find model errors. Use short horizons, a critic, and always
  finish with a real-sim check, which our harness already does.
- **Reference code:** CuboiLeo/SuperMimic-Reproduced (MIT, mjlab, torch) exists as a reference for details only.
  Third-party code is read, not run, unless vetted.
