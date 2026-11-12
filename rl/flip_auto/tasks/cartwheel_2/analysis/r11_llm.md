# Round 11 (cartwheel_2): LLM analysis (step 2)

**One-line verdict (video):** the best cartwheel so far. It is a clean straight-arm cartwheel that lands, settles in about 0.5 s and then holds the final pose for the whole 5 s tail without visible motion; the only visible flaws are in the support phase (the robot runs a few frames ahead of the reference and the two wrists are twisted differently).

Inputs: `r11_quant.md` (A, A2 v1/v2, A3, B, C, S), `round_look.sh cartwheel_2 11 model_12500` (floor contacts, ankle z, labels), close-ups 36-47, 48-59, 60-71, 72-83, 84-95, 96-107 (full resolution), all 19 sheets 000-737.

## Frame by frame (model_12500)

| frames | what the robot does |
|---|---|
| 0-23 | stands with arms overhead; left knee bends 0.20 -> 0.87 rad while the reference keeps it at 0.06-0.11; the left ankle rises at most 1.6 cm (0.051 vs 0.035 m), so the left foot stays down |
| 24-47 | lunge; torso goes horizontal, left hand reaches for the floor (left wrist on the floor from step 47, reference 53) |
| 48-59 | straight-arm support; the robot is visibly ahead of the green reference (inverted at 56-57 where the reference is still at about 45 deg) |
| 60-71 | both palms on the floor (wrist_yaw contact 47-74 left / 57-77 right vs reference 53-69 / 58-72); legs pass over the top; head clear of the floor |
| 72-83 | the right foot lands first (step 72, reference 73); the left foot stays in the air until step 86 (reference 108 by contact, but its ankle is already at 0.10 m at step 92) |
| 84-95 | rises to standing, arms forward; wide stance; the robot is beside the reference by about one body width |
| 96-131 | upright wide stance, arms overhead, matches the reference's final pose (hold tilt error 4.9 deg) |
| 132-737 | no visible motion on any sheet (pelvis speed max 0.05 m/s, drift 0.002 m in the hold window) |

## Measured, r09 -> r10 -> r11

| metric | r09 | r10 | r11 |
|---|---|---|---|
| robust dr v2 / v1 | 0.992 / 0.957 | 0.879 / 0.82 | 0.992 / 0.938 |
| robust 20 ms v2 / v1 | 0.941 / 0.762 | 0.707 / 0.59 | **0.961** / 0.805 |
| robust kp x0.85 v2 / v1 | 0.996 / 0.938 | 0.871 / 0.809 | 0.988 / 0.93 |
| robust 40 ms v2 | - | - | 0.453 (not a gate) |
| hold tilt error (deg, gate 5) | 6.1 | 6.7 | **4.9** |
| hold pose error (rad) | 0.072 | 0.054 | 0.057 |
| tracking body error (m) | 0.062 | 0.052 | 0.056 |
| critic worst unwaived (gate 3) | 4.98 | 3.45 | 3.86 |

All gates pass for the first time except `critic_clean` (3.86) and the two sim2sim gates (not run yet).

## Diagnosis

- The rollback worked: removing `agent_r10_hold_posture` restored the robustness, and 1500 more iterations from r09 pushed 20 ms latency over the gate (0.941 -> 0.961). Hold tilt fell 6.1 -> 4.9 without any posture term. In r10 a joint term was the wrong tool; tilt improved here with continued training alone.
- Critic checks above 3 (gate fails on the first, the others are next in line):
  - `asymmetry:wrist_roll:support` 3.9: left/right wrist roll differ 54 deg vs reference 16 deg. Its current fix (dyn_sym, std 0.2) would give signal 0.034 at this error, so it has practically no gradient. The close-ups 60-71 show the cause: the left hand is turned in while the right palm is flat.
  - `jitter:all:settle` 3.4: mean action change 0.169 in settle (quiet < 0.05); on the sheets this is the quick stand-up 88-100.
  - `asymmetry:hip_yaw:support` 3.2: 46 vs 14 deg.
  - `jitter:wrist_roll:land` 3.1, with its fix active at weight 1 (r10 2.3, r11 3.1: the fix holds it near 3, not below).
  - `contact:right_foot:land` 3.0 (at the threshold, passes).
- All five live in support / land / settle. None is in `stand_after`, where r10 showed that pinning terms cost robustness.

## Decision for round 12

- init r11 `model_12500`. Keep everything in r11.
- Library fixes, all gated to support / land / settle, with std set so the error gives a real gradient:
  - `asymmetry:wrist_roll:support` weight 1, std 0.6 (signal 0.03 -> 0.33);
  - `asymmetry:hip_yaw:support` weight 1, std 0.5 (signal 0.06 -> 0.33);
  - `jitter:all:settle` weight 1;
  - `jitter:wrist_roll:land` weight 1 -> 2.
- In parallel (CPU, no GPU needed): the sim2sim exam on r11 `model_12500`. `sim2sim/native_flip.py` is backflip-only (success rule rotation >= 330 deg, takeoff from the `flight` phase, no hand friction, no `sim2sim_<ck>.json`), so it gets a cartwheel-capable success rule first: the same rule as A2 v2 (rotation >= 0.9 x reference, upright, pelvis > 0.6 m, drift < 0.5 m).
- Rollback (rule set when r12 was launched): if any robust v2 gate (dr / 20 ms / kp) < 0.95 or any hold gate fails, r11 `model_12500` stays the candidate. If the critic is still above 3 after r12 with all five fixes active, the remaining checks are reviewed one by one for a waiver rather than more reward terms.

## Addendum (2026-11-02, after r12 was launched): sim2sim exam of r11 model_12500

Native MuJoCo 3.5 (CPU, float64), `sim2sim/native_skill.py` on `models/cartwheel.mjb` (hand friction 0.6, knees 120 N.m),
same success rule as robust v2, 100 jittered starts per scenario + the exact start:

| scenario | success | rotation p50 (ref 255.5) | hold tilt p95 | hold drift p95 (m) | knee max (N.m) |
|---|---|---|---|---|---|
| nominal | 1.00 | 270.8 | 15.7 | 0.005 | 102.8 |
| lat20 (gate delay20) | 1.00 | 272.1 | 16.1 | 0.009 | 105.7 |
| lat40 | 1.00 | 256.5 | 17.1 | 0.010 | 118.6 |
| fric0.5 / fric1.0 | 1.00 / 1.00 | 270.9 / 270.6 | 15.9 / 15.6 | 0.005 / 0.004 | 102.8 / 107.8 |
| kp085 | 1.00 | 279.7 | 16.9 | 0.002 | 114.0 |
| push_pre / push_post | 1.00 / 1.00 | 271.4 / 270.6 | 16.0 / 17.3 | 0.006 / 0.035 | 107.7 / 102.8 |

Both sim2sim gates pass (`sim2sim_model_12500.json`); re-evaluated stop criteria: r11 fails only critic_clean (3.86).
Caveat: each native scenario has one perturbation alone. mjlab's robust delay2 (40 ms on top of the full training
randomisation) is 0.453, while native lat40 alone is 1.00. The native suite is milder than the mjlab dr scenarios, not
a contradiction.
