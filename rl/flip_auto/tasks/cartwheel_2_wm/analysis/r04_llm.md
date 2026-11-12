# Round 4 (world-model trainer, warm start from r03) - analysis (step 2)

**One-line verdict:** for the first time the robot bends over and puts both hands on the floor (steps 40-50), but the
legs do not go over. It tips sideways at steps 52-56, lies on its side with one leg up, and ends prone and still.

## Round incidents (framework, not the decision)

- **GPU fault.** Training died at minute 50.8 with CUDA error 999 (`cuStreamSynchronize`).
  - No guard had fired (all counters 0).
  - Windows logs show no driver reset; after the processes exited, CUDA + Warp self-tests pass.
  - The exported checkpoints are model_2294 (min ~20) and model_2940 (min ~40). The best evaluated checkpoint, 2294,
    is effectively a 20-min policy.
- **The harness stopped in protocol step 1 (robust.sh, same CUDA fault).** I ran the remaining step-1 commands by hand,
  identical to harness.py lines 511-517: robust, segments, analyze_round, quant_report.
- **Framework bug found and fixed (harness.py, quant_report.py).**
  - The segment probe was called with the clip (`cartwheel_2`) instead of the task (`cartwheel_2_wm`). For this task
    it therefore read the PPO run's state: section A3 of r02_quant / r03_quant probed the PPO r02 model_1499 / PPO r03
    model_2998, not the WM policies.
  - Fixed: the harness passes TASK, and quant_report reads `segments_<TASK>_*`. For the PPO task, TASK == CLIP, so
    nothing changes there.
  - The WM r03 probe was rerun on model_1812, and r03_quant.md was regenerated. The version used for the r04 decision
    is kept as r03_quant_segbug.md.

## Video (r04_model_2294, all 13 sheets 000-487 reviewed)

| steps | what the robot does |
|---|---|
| 0-39 | stand and lunge close to the reference |
| 40-50 | bends forward, both hands reach the floor (r03: stayed upright, arms out, fell backwards) |
| 51-56 | legs do not rise; tips over sideways |
| 57-100 | on its side, one leg raised and swept down |
| 101-487 | prone, still |

## Quantitative (r04_quant.md)

**Eval:**

| checkpoint | rotation | landed | robustness |
|---|---|---|---|
| model_2294 | 142 deg | False | 0 / 5 (rotation p50 145 deg) |
| model_2940 | 97.5 deg | False | - |
| r03 model_1812 | 196 deg | False | - |

**Segment probe (WM policies, corrected):**

| start | r03 model_1812 | r04 model_2940 |
|---|---|---|
| 0 | lost at frame 42 | lost at frame 48 |
| 16 | lost at frame 41 | lost at frame 57 |
| 30 | lost at frame 46 | lost at frame 55 |
| 46 / 60 | lost within 12-19 steps, never kept | lost within 12-19 steps, never kept |
| 115 (stand) | never lost 0.48 | never lost 0.83 |

- The lunge is held about 10 frames longer than in r03. The support phase is not learned at all yet.

**Training:**
- Mean episode length at the end 28 (r03: 39). The reference changed, so the numbers are not directly comparable.
- No NaN, and the guards never fired.

## Comparison with PPO (corrected)

| run | segment probe | hands on the floor |
|---|---|---|
| PPO r02 | start 60 never lost 0.75 (second half learned) | no |
| PPO r03 | first full success at model_2500 | yes |
| WM r03 | support never kept | no |
| WM r04 | support never kept | yes (video), but nothing learned after the entry |

- **Correction of r03_llm.md and of my earlier chat answer.** "The WM r03 support phase is kept 1.0" was wrong: those
  numbers were the PPO r03 policy.

## -> r05

- **Keep the r04 knobs.** The reference with planted palms produced the hands-on-floor entry that r04 expected.
- **r04 rollback_if is not met.** Rotation is lower, but the fall is not earlier (sideways at 52-56, versus backwards
  at 48-55).
- **Warm start** from r04 model_2940 (the last checkpoint, which holds the lunge longest), with its full trainer state.
- The round gets 60 min again.
