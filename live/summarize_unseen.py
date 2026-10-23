"""No-prior test summary (routine playback): per video, which dance each replay was started for (the recognition
decision that matters), how long after the first sight of the person, and falls.
Ground truth: file name for unseen_*, the user's clip (user_1) is 闪身步 (checked by eye),
unseen_switch = 闪身步 7.5 s -> 狗熊哆嗦毛 8.5 s -> 闪身步 7.8 s.
Usage (any python): python summarize_unseen.py
"""
import re
from pathlib import Path

D = Path(__file__).resolve().parents[1] / "videos" / "follow"
TRUTH = {"user_1": 0, "unseen_sss_1": 0, "unseen_sss_2": 0, "unseen_sss_3": 0,
         "unseen_gxdsm_1": 1, "unseen_gxdsm_2": 1, "unseen_gxdsm_3": 1}
EN = {"Shan Shen Bu": 0, "Gou Xiong Duo Suo Mao": 1}
NAME = {0: "闪身步", 1: "狗熊哆嗦毛"}
trig = re.compile(r"event t=\s*([\d.]+)s recognised (.+?) -> full replay")
pred = re.compile(r"\[trace\] t=\s*([\d.]+) mode=")
fell = re.compile(r"event t=\s*([\d.]+)s fell")

print(f"{'video':<16} {'truth':<6} {'replays':>7}  replay choices (sim time)")
tot, ok_tot = 0, 0
for name in list(TRUTH) + ["unseen_switch"]:
  f = D / f"follow_{name}_trace.txt"
  if not f.exists():
    print(f"{name:<16} (not run)")
    continue
  lines = f.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
  tr = [(float(m.group(1)), EN[m.group(2)]) for m in (trig.search(l) for l in lines) if m]
  first = min([float(m.group(1)) for m in (pred.search(l) for l in lines) if m] + [t for t, _ in tr] or [0.0])
  falls = sum(1 for l in lines if fell.search(l))
  if name == "unseen_switch":
    truth = lambda t: 0 if t - first < 7.5 else 1 if t - first < 16.0 else 0  # noqa: E731
    lab = "switch"
  else:
    truth = lambda t, v=TRUTH[name]: v  # noqa: E731
    lab = NAME[TRUTH[name]]
  ok = sum(d == truth(t) for t, d in tr)
  tot, ok_tot = tot + len(tr), ok_tot + ok
  desc = ", ".join(f"{t - first:.1f}s {NAME[d]}{'' if d == truth(t) else ' (WRONG)'}" for t, d in tr)
  print(f"{name:<16} {lab:<6} {len(tr):>7}  {desc}{f'  | falls {falls}' if falls else ''}")
print(f"\nreplays started for the right dance: {ok_tot}/{tot}")
