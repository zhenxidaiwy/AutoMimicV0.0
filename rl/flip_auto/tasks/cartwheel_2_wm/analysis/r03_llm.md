# Round 3 (world-model trainer, guarded) - analysis (step 2)

**One-line verdict:** the lunge is followed well, but the robot never gets onto its hands. It tips backwards at steps
44-52, lands on its back with one leg up, and lies still on the floor to the end. The jitter is gone.

## Video (r03_model_1812, all 13 sheets 000-487 reviewed)

| steps | what the robot does |
|---|---|
| 0-39 | stand and lunge close to the reference (arms up, then step and lean) |
| 40-47 | the reference reaches down for the hands; the robot stays upright, arms out sideways |
| 48-55 | the robot sits / falls backwards; hands never touch the floor in front |
| 56-80 | on its back, right leg raised and slowly lowered (the 196 deg rotation) |
| 81-103 | turns to its side, legs splayed |
| 104-487 | lies flat, completely still (post action change 0.0001; r01: 0.64) |

## Quantitative (r03_quant.md)

- **Eval:** score 1.537, rotation 196 deg (reference 255), landed False, robustness 0 / 5.
- **Segment probe (training randomisation):**
  - starts at support (46, 60) are kept 1.0 / 0.875;
  - starts at lunge (16, 30) are kept 0.86 / 0.95;
  - starts at land (81) are kept only 0.39.
- **The probe and the full-run eval disagree.** In the probe, a robot started inside the support phase can carry on;
  in the eval video, the robot never enters it from the lunge.
- **Training (no NaN in 60 min; all guard counters 0):**
  - real track step 1.56 -> 2.17;
  - falls per step 0.061 -> 0.027;
  - mean episode length 16 -> 39 (r01 ~70);
  - head reward MSE 26 -> 5.6.
- **The round 2 NaN did not reappear, and the guards never fired.** The r02 trigger is therefore not identified; the
  counters stay in the log.

## Comparison with the PPO run at the same point (cartwheel_2 r02 -> r03 decision)

- **Same failure.** PPO r02 also lost the entry onto the hands (start 46 lost within 5 steps).
- **PPO's diagnosis was a reference property:**
  - in the plant_vlm_hold reference the hands are 6-25 cm above the floor when the human's are down;
  - the root drops at 2 g at the foot -> hand switch.
- **PPO r03 fixed it with:**
  - the reachqp_vlm_hold reference (smooth root grounding, palms planted by the arm joints only);
  - priors lunge 3 / support 2;
  - a warm start.
- These are reference / reset properties, not trainer properties, so r04 applies them the same way.

## Correction (written after r04)

- The segment-probe numbers above came from the PPO run's r03 policy (model_2998), not from WM r03 (framework bug:
  segments.sh was called with the clip, not the task; fixed, see r04_llm.md).
- The WM r03 model_1812 probe:
  - lost at frames 41-46 from the lunge starts;
  - lost within 12-19 steps from the support starts (never kept 0.0);
  - stand-at-the-end never lost 0.48.
- So "the probe and the full-run eval disagree" was wrong: neither shows the support phase learned.
- The r04 decision did not use the probe numbers; it used the video and the PPO r03 fixes.

## -> r04

- Reference reachqp_vlm_hold, prior.lunge 3, prior.support 2.
- Warm start from r03 model_1812, through its full trainer state (state_1812.pt).
