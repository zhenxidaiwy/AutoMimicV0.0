"""Trigger rules with two recognisers: dance / canonical frame / confidence from the closed-set model, the 'other
motion' veto from the open-set model (ticks of both trigger_eval runs, same videos and tick times).
Usage: python combo_eval.py <closed watch> <open watch>"""
import itertools
import json
import sys
from pathlib import Path

import numpy as np

from trigger_eval import H, TRUTH, score

closed, opened = sys.argv[1], sys.argv[2]
R = H / "projects/dance/vla/trigger_eval"
tc = json.load(open(R / closed / "ticks.json"))
to = json.load(open(R / opened / "ticks.json"))
preds = {}
for n, ticks in tc.items():
  preds[n] = [{**a, "other": b.get("other", 0.0)} if a["vis"] == "ok" and b["vis"] == "ok" else a
              for a, b in zip(ticks, to[n])]
mf = np.load(H / "projects/dance/multi/canon_v1.npz")
names = [str(x) for x in mf["clip_names"]]
lens = {n: int((mf["clip_id"] == i).sum()) for i, n in enumerate(names)}
clip_s = {0: (lens["bda_zhao_sss"] - 3) / 50, 1: (lens["bda2_gxdsm_full"] - 3) / 50}
res = []
for hold, conf, adv, oth, ostop in itertools.product((0.0, 0.3, 0.5), (0.7, 0.9), (0.0, 0.3), (0.3, 0.5, 0.7, 0.9, 1.01),
                                                    (0.9, 1.01)):
  r = {"name": f"hold {hold} conf {conf} adv {adv} oth {oth} stop-oth {ostop}", "hold": hold, "conf": conf,
       "adv": adv, "back": 6, "other": oth, "other_stop": ostop}
  s = score(preds, r, clip_s)
  pv = {k: v for k, v in s["pos"].items() if TRUTH.get(k, "?") not in ("?", None)}
  lat = [v["first_t"] for v in pv.values() if v["first_t"] is not None]
  res.append({**r, **{k: s[k] for k in ("neg_triggers", "neg_clips_triggered", "neg_robot_dance_s")},
              "hit": sum(v["n"] > 0 for v in pv.values()), "right": sum(bool(v["right"]) for v in pv.values()),
              "wrong": sum(v["wrong_n"] for v in pv.values()), "t_med": round(float(np.median(lat)), 2) if lat else None,
              "neg": {k: v["n"] for k, v in s["pos"].items() if TRUTH.get(k) is None and v["n"]},
              "miss": [k for k, v in pv.items() if not v["n"]],
              "pos_dance_s": None})
res.sort(key=lambda r: (-r["right"], r["neg_triggers"], r["neg_robot_dance_s"], r["t_med"] or 99))
(R / f"combo_{closed}_{opened}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(f"{'rule':<52} negTrig negClips negDance_s | hit right wrong t_med | negatives triggered / positives missed")
for r in res[:20]:
  print(f"{r['name']:<52} {r['neg_triggers']:>7} {r['neg_clips_triggered']:>8} {r['neg_robot_dance_s']:>10} | "
        f"{r['hit']:>3} {r['right']:>5} {r['wrong']:>5} {r['t_med']} | {r['neg']} / {r['miss']}")
