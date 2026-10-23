"""Held-out check of the trigger on negatives that played no part in tuning or training (neg_10.. = batch 2) and on
the positive videos; old 1-recognition rule vs the chosen vote with a veto recogniser; 4 jitter seeds.
Usage (unitree_rl_mjlab env): python heldout_eval.py <veto open model, e.g. open_s0> [first_neg=10] [other_mean ...]"""
import sys

veto = sys.argv[1]
first = int(sys.argv[2]) if len(sys.argv) > 2 else 10
oms = [float(x) for x in sys.argv[3:]] or [0.7]
sys.argv = [sys.argv[0], "--open", veto]  # robust_eval parses its own args and computes the ticks at import
from robust_eval import clip_s, runs  # noqa: E402
from trigger_eval import TRUTH, simulate  # noqa: E402

RULES = {"old: 1 recognition, conf 0.7": {"conf": 0.7}}
for om in oms:
  RULES[f"vote 0.8/0.7/0.5 conf 0.9 adv 0.3 + {veto} mean other >= {om}"] = {
    "vote": True, "win": 0.8, "frac": 0.7, "span": 0.5, "conf": 0.9, "adv": 0.3, "back": 6, "other_mean": om}
negs = sorted((n for n in runs[0] if n.startswith("neg_") and int(n[4:]) >= first), key=lambda n: int(n[4:]))
poss = [n for n in runs[0] if TRUTH.get(n, "?") not in ("?", None)]
for rn, rule in RULES.items():
  sim = {n: [simulate(p[n], rule, clip_s) for p in runs] for n in negs + poss}
  nt = {n: [len(x) for x in sim[n]] for n in negs}
  ds = sum(r[2] - r[0] for n in negs for x in sim[n] for r in x)
  right = sum(bool(x) and x[0][1] in TRUTH[n] for n in poss for x in sim[n])
  print(f"{rn}:\n   held-out negatives: {sum(map(sum, nt.values()))} false triggers ({len(negs)} videos x {len(runs)} "
        f"seeds), {sum(any(v) for v in nt.values())}/{len(negs)} videos, robot dancing {ds:.1f} s | positives right "
        f"{right}/{len(poss) * len(runs)}")
  print("   negatives triggered:", {n: v for n, v in nt.items() if any(v)})
  print("   positives missed/wrong:", {n: sum(not (x and x[0][1] in TRUTH[n]) for x in sim[n]) for n in poss
                                     if any(not (x and x[0][1] in TRUTH[n]) for x in sim[n])})
