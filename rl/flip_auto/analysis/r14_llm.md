# Round 14 - LLM analysis (step 2; step 3 = decisions/r15.json)

Inputs: analysis/r14_quant.md (automatic + section A2 robustness, added this round), all five every-step sheets,
mjlab tracking event config (dr_show.sh).

## 1. Expectations from decisions/r14.json vs result

| expectation | r13 | r14 | met? |
|---|---|---|---|
| track_joint_err < 1.4 | 1.52 | 1.50 | no (diminishing) |
| track_body_err < 0.065 m | 0.073 | 0.064 | yes |
| take-off shoulder-yaw sev < 3 | 4.9 | 4.5 | no |
| stand pelvis speed < 0.3 | 0.047 | 0.076 | yes |
| action change < 0.1 | 0.039 | 0.053 | yes |
| rotation >= 345, upright | 367 | 365, end tilt 1.9 | yes |
| (not targeted) plane deviation | 9.3 | 6.4 | better |

Sheets: robot covers the reference in stand, crouch and after landing (the ghost is barely visible from step ~150);
flight as r13. The fidelity curriculum has converged: x2.25 -> x3.375 bought 0.02 rad of joint error.

## 2. Robustness (new tool, eval_flip_robust.py, 256 envs per scenario)

| scenario | success | fell |
|---|---|---|
| nominal | 1.00 | 0 |
| training randomisation (pushes, friction 0.3-1.2, CoM, encoder bias, obs noise) | 1.00 | 0 |
| PD stiffness x0.85 | 1.00 | 0 |
| action delay 20 ms | 0.70 | 0.26 |
| action delay 40 ms | 0.00 | 0.90 |

The tracking task trains with pushes, friction, CoM offset, encoder bias and observation noise (dr_show.sh) - and the
policy is robust to all of them - but with NO control latency. A real G1 has roughly 10-20 ms between state reading
and the motor command; at 20 ms a quarter of the flips end on the floor. This, not wrist fidelity, is the gap to the
real robot.

## 3. Priorities

| P | item | why |
|---|---|---|
| P1 | latency robustness | 26 % falls at 20 ms: blocks deployment on the real G1 |
| - | further fidelity (wrists, take-off arm yaw) | converged / cosmetic |

## 4. Solution (-> decisions/r15.json)

- New sim-to-real knob delay_ms: every actuator wrapped in mjlab's DelayedActuatorCfg, position target delayed by
  0..25 ms per env (0..5 physics steps, held with p = 0.9) during training (flip_rewards.add_action_delay,
  train_dance --delay-ms, harness knob `delay_ms`).
- Harness: robustness evaluation (robust.sh) now runs automatically after every round and appears in section A2.
- Keep tracking at x3.375 / x0.614 and all other terms; start from r14 model_12000.
- Expect: delay 20 ms success >= 0.95, delay 40 ms >= 0.5; nominal / dr / kp stay 1.0; fidelity held
  (track_body_err < 0.075, rotation >= 345, stand quiet).
- Rollback: nominal success < 1.0 or rotation < 340 -> r16 from r14 model_12000 with delay_ms 15.
