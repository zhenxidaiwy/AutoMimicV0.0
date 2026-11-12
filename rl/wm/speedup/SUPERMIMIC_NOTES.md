# SuperMimic: what the paper actually does, and where this branch differs (2026-11-02)

Source: arXiv 2610.28480, read from the PDF. Section numbers are the paper's.

## The method (§3, Algorithm A.1, Table A.5)

**One online loop (Dyna style), every iteration:**

1. **Collect.** The current policy runs in MuJoCo Warp (4096 envs per GPU) with action noise N(0, 0.1²). The
   executed noisy action is stored, and transitions go into a replay buffer of 1000 steps per env (oldest out).
   Resets use return-based sampling over 1 s bins: 50 % uniform, 40 % softmax(-25 G_b / G_max) favouring
   low-return bins, 10 % past weights.
2. **Fit the world model.** k = 8 autoregressive windows from the buffer, seeded at logged states and rolled on
   logged actions.
   - Loss: state + reward + noise-free observation + termination BCE.
   - "Each head is either learned or computed analytically". An analytic head has no loss term.
   - Dynamics MLP (2048, 2048, 2048). Adam 2e-4, batch 10 x 2048 windows, global grad clip 1.0.
3. **Improve the policy** through the frozen model.
   - **Start states:** 4096 rollouts per update, each starting from a **replay-buffer state** with its sim
     context ξ.
   - **Rollout:** H = 32 imagined steps. Sensor noise is re-added to the predicted noise-free observation.
   - **Objective:** Ĵ = Σ_{t<H} γ^t ĉ_t r̂_{t+1} + γ^H ĉ_H V(ŝ_H, g_H, ξ), with γ = 0.99. The soft survival
     ĉ_{t+1} = ĉ_t (1 - d̂_{t+1}) uses the *learned termination probability*, which keeps it differentiable.
   - **Actor optimiser:** Adam β = (0.9, 0.95), lr = the world model's (2e-4). Grad clip: global norm 1.0, then
     element-wise 0.1.
   - **Critic:**
     - Input (ŝ, g, ξ), MLP (256, 128).
     - Target: GAE, λ = 0.95, computed once per rollout. No target network.
     - Training: 5 epochs x 4 shuffled minibatches per update; Adam, same lr, clip 1.0.

**Schedule and results:**

- Update-to-data ratio 0.4; 1 policy update per world-model update.
- Cosine lr decay to 0.03x over 250 k iterations; 320 k iterations in total.
- The policy is trained **from scratch** (motion encoder + decoder).
- "3 h on one H100" covers the **whole loop**, simulator collection included.
- Critic ablation (§4.3): without a critic, H ≤ 16 fails. With it, H = 16 matches critic-free H = 32. Only the
  critic policy recovers from pushes.

## This branch so far vs the paper

| item | paper | branch (E1 v0) | status |
|---|---|---|---|
| data | online buffer, refreshed every iteration by the current policy | one offline dataset (61 past checkpoints), model frozen | **deviation**: the main one |
| model fit | continual, k = 8 | offline v1b, k = 8 | same idea, offline |
| reward head | learned or analytic | analytic (exact FK) | allowed by the paper |
| termination | learned probability, soft survival | analytic hard checks (no gradient at the boundary) | deviation |
| rollout start | replay-buffer states (the policy's own distribution) | reference states (RSI), carried over or fresh | **deviation** |
| sensor noise in imagination | re-added | none | deviation |
| actor optimiser | Adam (0.9, 0.95), 2e-4, clip 1.0 + element-wise 0.1 | Adam default betas, 5e-5, clip 1.0 | deviation |
| critic | (ŝ, g, ξ), (256, 128), GAE 0.95, 5 x 4 minibatches | (obs, t), (512, 256, 128), TD(λ), 2 epochs | deviation |
| policy | from scratch | fine-tune of a PPO checkpoint | deviation (E1 is a fine-tune test) |
| model size | 3 x 2048 | 3 x 1024 (8 GB laptop) | resource limit |

## Results 2026-11-03 (all real numbers are mjlab evals from r04 model_4497: e1.sh eval)

**E1, PPO vs offline BPTT (v0 shac.py).**

| policy | GPU time | `track_body_err_m` | `track_rew_step` |
|---|---|---|---|
| init | 0 | 0.0794 | 3.81 |
| BPTT, SGD 0.02, fresh RSI, no critic | 5 min | 0.0663 | 4.11 |
| PPO, 100 iterations | ~4.5 min | 0.0433 | 4.25 |
| PPO, 1500 iterations | 67 min | 0.0333 | 4.55 |

- No falls in any run.
- PPO wins the fine-tune.
- Throughput is equal: BPTT ~35 k imagined steps/s with gradients, PPO ~37 k sim steps/s. A forward-only rollout
  runs at 1.59 M steps/s; the backward pass costs ~45x.

**Gap check (check.py H32 on real rollouts of each policy).**
- Init, both BPTT runs, PPO 4600 and PPO 5996: imagined return is −2 to −5 % of real (corr ≥ 0.97).
- The model ranks all five policies in the true order.
- So for small policy steps the model is trustworthy, and it "knows" PPO's policy is better.

**Plan A (shac_paper.py, buffer = 965 k real states from r04, 4096 x 240, action noise 0.1, 83 s to collect).**

| run | imagined probe | real `track_rew_step` | real `track_body_err_m` | gap (imag vs real) |
|---|---|---|---|---|
| paper settings (critic, lr 2e-4, no warm-up) | 3.91 -> 3.60 in 1 min | not evaluated | not evaluated | not measured |
| + 40-iteration critic warm-up | 3.71 -> 3.81 -> 3.02 | not evaluated | not evaluated | not measured |
| A1: critic, lr 2e-5 | 3.71 -> 3.87 | 3.39 | 0.078 | +5 % |
| A2: no critic, lr 2e-4 (2.6 min / 5 min) | 3.71 -> 4.30 | 3.12 / 3.50 | 0.565 / 0.551, falls | +22 % / +17 % |

The no-warm-up run: reward falls from iteration 4.

**Reading.**
- With paper-sized steps the policy leaves the buffer distribution within minutes and exploits the frozen model:
  imagined return is overestimated by 17-22 % and the real policy falls.
- With small steps (Adam 1e-5) it stays in distribution, but the gain is slow.
- A frozen model cannot have both. This is what the paper's online loop exists for, so Plan B is the real test.
- New deviation found: in a fine-tune the fresh critic's gradients pull the actor down, even after warm-up. The paper
  trains actor and critic together from scratch.

## Plan B result 2026-11-03: online loop from scratch vs the harness PPO from scratch (online.py, run b_online_v1)

**Setup.**
- Everything from scratch: policy, world model, critic. 4096 envs, 4096 rollouts, H 32, model 10 x 2048 windows
  per iteration, return-based resets.
- 60 min, 2295 iterations. Time split: 631 s collect, 748 s model fit, 2182 s policy update. Peak 5.2 GB.
- Policy update: batched FK with analytic velocities (equal to the jvp version to 1e-5) plus torch.compile, 4.3 ->
  0.9 s per 4096 x 32 update. Imagination with gradients is ~2.5x faster than mjlab; the paper reports > 10x.
- Lenovo performance mode: GPU power 32 -> 88 W, iteration time unchanged at 1.54 s. The loop is bound by kernel
  launches on the CPU side.
- Eval: e1.sh eval, the same reference (reachqp) for every checkpoint. The harness rounds r01 / r02 trained on the
  older g1_lock reference with flip terms, ~3.77 s per iteration.

`track_rew_step` by GPU time:

| GPU time | Plan B | PPO r01 | PPO r02 |
|---|---|---|---|
| ~6 min | 2.33 | — | — |
| ~16 min | 2.87 | — | — |
| ~31 min | 2.69 (best 2.91 at 36 min) | 3.21 (it 500) | 3.49 (it 500) |
| ~60 min | 2.53 | 3.69 (it 1000) | 3.76 (it 1000) |
| ~94 min | — | 3.71 (it 1499) | 3.75 (it 1499) |

**Other metrics.**
- Falls per 1000 steps: Plan B 0.10-0.20; PPO 0-0.05.
- No checkpoint of either method completes the cartwheel and stands. The harness PPO first does at r04, 4.7 h.

**Verdict.**
- At laptop scale on one clip, the SuperMimic loop does not shorten GPU time. It plateaus after ~15 min, below PPO
  at every matched time.
- What this does not show: the paper's regime (many motions sharing one model, 3 x 2048, 320 k iterations on an H100).
- Untested suspects in this implementation:
  - model and critic norms are fixed from the random-policy warm-up data;
  - the model is half the paper's size;
  - the analytic soft termination.
- Recommendation recorded with the user: stop the training-speedup line. Reuse the world model for pre-screening
  (it ranks policies correctly, PLAN_v1 P3).

## Pretrained world-model init for the online loop, 2026-11-04 (online.py --wm-init, 60 min each)

**Models.**
- **v1b:** our 3 x 1024 model. Its training data includes 14 cartwheel files from r01-r10, so it is optimistic.
- **v1c:** the v1b recipe with all cartwheel data held out.
- **CuboiLeo e8:** 3 x 2048, BONES-SEED, 100 k iterations, 28 GPU-h on 4 x 5090.
  - Loaded through cuboi_wm.py: re-implemented, weights only, PosixPath the only allow-listed global.
  - Their mjlab is 1.6.0, ours 1.2.0.
- Held-out cartwheel open loop (compare_wm.py):

  | horizon | e8 tilt | v1b tilt | e8 joints | v1b joints |
  |---|---|---|---|---|
  | H1 | 0.23 deg | 0.51 deg | 0.0033 | 0.0067 |
  | H32 | 9.3 deg | 3.6 deg | 0.055 | 0.029 |

**`track_rew_step` (e1.sh eval) by GPU time:**

| GPU time | scratch | v1b | v1c | CuboiLeo | PPO r02 |
|---|---|---|---|---|---|
| ~6 min | 2.33 | 2.28 | 1.89 | 2.16 | — |
| ~16 min | 2.87 | 2.44 | 1.94 | 2.87 | — |
| ~26 min | 2.82 | 1.75 | 2.03 | 2.91 | — |
| ~31-36 min | 2.69-2.91 | 1.96 | 1.85 | 2.95 | 3.49 |
| ~47 min | 2.28 | 2.26 | 1.88 | 3.07 | — |
| ~60 min | 2.53 | 2.18 | 2.04 | 2.71 | 3.76 |
| iterations in 60 min | 2295 | 2286 | 2405 | 414 | ~950 |

**Reading.**
- The CuboiLeo init learns most per update: 3.07 after ~330 updates.
- Its 3 x 2048 model costs 7 s per policy update on the 8 GB laptop (not compiled), against 0.9 s for 3 x 1024. So it
  gets one sixth of the updates.
- At matched GPU time it stays 0.5-1.0 below PPO, and its 60-min point drops back.
- Our own pretrained models (v1b, v1c) do not help. Both are below scratch, and the online fit is unstable: v1b's
  model loss rises 0.15 -> 0.75 late in the run.
- **Verdict:** no init makes the loop beat PPO on this laptop.
- **Open:** CuboiLeo init with fast updates (bigger GPU, or compile + bf16), untested.

## Plan to follow the paper (laptop-sized)

- **A. Policy update as in the paper**, offline buffer for now:
  - start states from logged buffer states;
  - critic as in the paper;
  - Adam (0.9, 0.95) with the two-stage clip;
  - sensor noise;
  - a soft survival weight from a learned termination head (or an analytic soft margin, stated as such).
- **B. The online loop:** mjlab collection with the current policy -> buffer -> continual model fit -> policy
  update, sized for 8 GB (fewer envs).
  - Wall time includes collection, as in the paper.
  - This is the faithful speed test.
