# Branch `wm-speedup`: does a world model shorten training? (feasibility, 2026-11-02)

## Question

SuperMimic's claim, tested on our setup: training a policy by backprop through a learned world model (BPTT, SHAC-style)
reaches a given tracking quality in much less GPU time than PPO in the simulator.

Scope:

- Only the speed question. The harness, library and LLM loop on `main` stay unchanged.
- Everything new lives in `rl/wm/speedup/`.
- **Verdict = real mjlab evaluation.** Imagined numbers never count as results.

## Approach

The policy is trained in imagination on the same observation and reward as mjlab's tracking task, so a checkpoint
trained there loads and runs in mjlab unchanged.

| piece | how |
|---|---|
| dynamics | v1 world model (`wm_runs/v1_h1024/wm.pt`), frozen |
| world root pose | integrate the predicted (dyaw, dx, dy); height and tilt come from the state |
| body poses | differentiable torch FK of the G1 (from the mjlab `g1.xml` MjModel) from root pose + joint angles. Exact, so no learned body head is needed. Body velocities by finite difference |
| actor observation | exactly mjlab's `Unitree-G1-Tracking-No-State-Estimation` actor terms: command (ref joint pos + vel), anchor ori in robot torso frame, pelvis ang vel, joint pos / vel rel, last action |
| reward | mjlab tracking terms: anchor pos / ori, relative body pos / ori, body lin / ang vel, action rate, joint limits. Self-collision is left out |
| termination | the task's geometric checks on FK poses (anchor z, anchor ori, end-effector z) |
| delay | per-env 0-2 step action delay, as in the collected data |
| policy update | SHAC: H = 32 imagined steps, a critic for the value beyond H, 4096 rollouts per update; the actor is initialised from the PPO checkpoint |

## Steps and gates

| step | work | gate (go / no-go) |
|---|---|---|
| S1 | `fk.py`: torch FK | Body positions / quats vs the logged ones in `wm_data/v1`: < 1 mm, < 0.5 deg |
| S2 | `imagine.py`: imagined tracking env | Run an existing PPO policy closed-loop in the model and in mjlab from the same start states. The per-step tracking reward must correlate over 32 steps, and its mean must be within 10 % |
| S3 | `shac.py`: BPTT trainer + export to an rsl_rl checkpoint | A smoke run improves the imagined return; the exported checkpoint loads in mjlab |
| E1 | cartwheel_2, from mid-training checkpoint r04 `model_4497` (track 0.074 m). **PPO arm:** plain tracking task, same init, 1500 iterations. **BPTT arm:** same init. Both evaluated with `eval_flip` in mjlab every N minutes | **Feasible if BPTT reaches PPO's final real tracking error in <= 1/3 of PPO's GPU time.** Data collection (19 min) and model fit (33 min) are reported separately, as a one-off cost shared across skills |
| E2 | only if E1 passes: a skill the model has never seen (leave-one-skill-out model), init from scratch or from another skill | same criterion |

**Stop rule:** if S2 fails (closed-loop drift too large), stop. Report why, and what the model would need (3 x 2048,
more data, termination head), before any BPTT.

## Honesty notes

- The v1 model was trained on data from 16 cartwheel_2 checkpoints, r04 among them. E1 therefore tests
  "fine-tune inside covered data". Generalisation is E2's job.
- The PPO arm uses the plain tracking reward, not the harness knobs, so both arms optimise the same objective.
