# Resuming the get-up self-iteration harness

**Latest park: 2026-10-21 ~17:00 (user shut down the laptop), mid-round 9.** `park_now.sh` kept the half-trained
round: state.json says next round 9, warm start `2026-10-21_16-40-30_auto_r09_part1/model_24100.pt` (knobs of round
9: still_sigma_scale 3, w_still_bonus 6.9, ...). Best finished round so far: round 5 (score 8.67); round 8 scored
8.61. Every round now fine-tunes at lr 3e-4 (see REPORT.md "Root cause of the repeated collapses").
Resume exactly as below with `resume.sh`; stop immediately again with `park_now.sh` (keeps progress) or at the next
round boundary with `park.sh`.

---
Older notes:

Parked 2026-10-21 01:00 after round 2 (rounds 0-2 done). GPU idle, nothing running.

- State: `~/projects/dance_logs/auto/state.json` — next round 3, warm start
  `2026-10-21_00-13-24_auto_r02/model_20999.pt` (best so far, score 8.23, 9/12 targets).
- Lineage: round 2 continued from the user's pick `v7f model_19500` (packaged in `policies/getup_v7f_19500/`).
- Report with every round's numbers / knob changes / video names: `rl/auto/REPORT.md`; videos `videos/getup/auto_rNN.mp4`.

Resume (from Windows PowerShell, run in the background; takes ~45 min per round):

    wsl -d Ubuntu-22.04 -- bash /home/user/dance_win/rl/auto/resume.sh 10 1500

Stop cleanly at the next round boundary (keeps the finished round, drops the half-started one):

    wsl -d Ubuntu-22.04 -- bash /home/user/dance_win/rl/auto/park.sh

Open items after round 2: squat match 0.20 (target 0.5), standing template 0.78 / 0.88 from a standing start
(target 0.9) — the harness already raised w_squat 6 -> 9, squat_prob 0.2 -> 0.25, w_stand_template 6 -> 7.8.
Proposed (not yet approved by the user): add joint noise +-0.6 rad and random-orientation drops to training
(generalisation test of v7f 19500: 84% / 92% success there, see `rl/auto/gen_test.py`).
