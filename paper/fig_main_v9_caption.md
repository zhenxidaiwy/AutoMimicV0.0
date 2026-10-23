# Figure 1 (v9) — AutoMimic (working name)

v9 = v8 with panel (c) redrawn as the three-level diagnostic library implemented on 2026-10-23
(rl/flip_auto/library.py v2): L0 generic (any motion), L1 family (aerial skills), L2 task (this clip). Every newly
found failure enters L2; a fix verified on >= 2 tasks is promoted up (family, then generic); the stop criteria
(rl/flip_auto/stop_criteria.json) are layered the same way. Rows are real library entries: L0 = reward gated off at
a phase switch (r09-r11, fixed r12), template std much smaller than the error (r08), failure at 20 ms latency
(r14, fixed r15); L1 = spread termination, momentum repair, stricter airborne metric; L2 = tuck, hand-written leg
twist termination. "Next skill" now "inherits L0 + its family's L1 priors". Files: fig_main_v9.* ; v1-v8 unchanged.

Caption change (panel c): "(c) Every newly found failure becomes a (signature, fix) entry of a three-level library -
generic, motion family, task. Fixes verified on two or more tasks are promoted to the family and then the generic
level, so the next skill starts from the generic and family priors; the stop criteria are layered the same way."

(v8 notes below unchanged)
