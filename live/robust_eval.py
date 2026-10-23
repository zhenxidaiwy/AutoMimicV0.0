"""Trigger rules under live-like jitter (trigger_eval.predict_video with jitter seeds: dropped frames, tick phase /
jitter), closed-set recogniser for dance + frame, optional open-set recogniser as 'other motion' veto.
Counts are summed over the seeds (positives: fraction of (video, seed) runs that trigger with the right dance).
Usage (unitree_rl_mjlab env): python robust_eval.py [--closed ret_lead0_s0] [--open open_s1] [--seeds 4]
"""
import argparse
import itertools
import json

import numpy as np
import torch

from trigger_eval import H, KP, OUT, TRUTH, RetrieveNet, predict_video, score

ap = argparse.ArgumentParser()
ap.add_argument("--closed", default="ret_lead0_s0")
ap.add_argument("--open", default="")
ap.add_argument("--seeds", type=int, default=4)
a = ap.parse_args()
dev = "cuda:0" if torch.cuda.is_available() else "cpu"


def load(w):
  ws = torch.load(H / "projects/dance/vla/runs" / w / "model.pt", weights_only=False, map_location=dev)
  if ws.get("open"):
    from train_retrieve_open import OpenNet
    net = OpenNet().to(dev).eval()
  else:
    net = RetrieveNet().to(dev).eval()
  net.load_state_dict(ws["model"])
  return net


nets = {"closed": load(a.closed)}
if a.open:
  nets["open"] = load(a.open)
names = sorted(p.stem for p in KP.glob("*.npz"))
runs = []  # one preds dict per seed
for seed in range(a.seeds):
  js = None if seed == 0 else seed
  pc = {n: predict_video(nets["closed"], dev, n, js) for n in names}
  if a.open:
    po = {n: predict_video(nets["open"], dev, n, js) for n in names}
    pc = {n: [{**x, "other": y.get("other", 0.0)} if x["vis"] == "ok" and y["vis"] == "ok" else x
              for x, y in zip(pc[n], po[n])] for n in names}
  runs.append(pc)
mf = np.load(H / "projects/dance/multi/canon_v1.npz")
cn = [str(x) for x in mf["clip_names"]]
lens = {n: int((mf["clip_id"] == i).sum()) for i, n in enumerate(cn)}
clip_s = {0: (lens["bda_zhao_sss"] - 3) / 50, 1: (lens["bda2_gxdsm_full"] - 3) / 50}

rules = [{"name": "live-old (1 tick, conf 0.7)", "conf": 0.7},
         {"name": "hold 0.5 conf 0.9 adv 0.3", "hold": 0.5, "conf": 0.9, "adv": 0.3, "back": 6}]
oms = (1.01, 0.95, 0.9, 0.8, 0.7, 0.6) if a.open else (1.01,)
for (win, frac, span), conf, adv, om in itertools.product(
    ((0.6, 0.6, 0.3), (0.8, 0.6, 0.4), (0.8, 0.7, 0.5), (1.0, 0.6, 0.5), (1.0, 0.7, 0.6)),
    (0.9,), (0.3,), oms):
  rules.append({"name": f"vote w{win} f{frac} s{span} c{conf} a{adv} om{om}", "vote": True, "win": win,
                "frac": frac, "span": span, "conf": conf, "adv": adv, "back": 6, "other_mean": om})
res = []
for r in rules:
  tot = {"neg": 0, "neg_s": 0.0, "pos_right": 0, "pos_n": 0, "wrong": 0, "lat": [], "neg_v": {}, "miss": {}}
  for preds in runs:
    s = score(preds, r, clip_s)
    tot["neg"] += s["neg_triggers"]
    tot["neg_s"] += s["neg_robot_dance_s"]
    for k, v in s["pos"].items():
      tr = TRUTH.get(k, "?")
      if tr is None:
        if v["n"]:
          tot["neg_v"][k] = tot["neg_v"].get(k, 0) + v["n"]
      elif tr != "?":
        tot["pos_n"] += 1
        tot["pos_right"] += bool(v["right"])
        tot["wrong"] += v["wrong_n"]
        if v["first_t"] is not None:
          tot["lat"].append(v["first_t"])
        else:
          tot["miss"][k] = tot["miss"].get(k, 0) + 1
  res.append({"name": r["name"], "rule": r, "neg_triggers": tot["neg"], "neg_dance_s": round(tot["neg_s"], 1),
              "pos_right": f"{tot['pos_right']}/{tot['pos_n']}", "pos_right_n": tot["pos_right"],
              "wrong": tot["wrong"], "t_med": round(float(np.median(tot["lat"])), 2) if tot["lat"] else None,
              "neg_videos": tot["neg_v"], "missed": tot["miss"]})
tag = f"robust_{a.closed}_{a.open or 'none'}"
(OUT / f"{tag}.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
print(f"{a.seeds} seeds (seed 0 = no jitter); counts summed over seeds")
print(f"{'rule':<40} negTrig negDance_s | posRight wrong t_med | negative videos / missed positives")
show = res[:2] + sorted(res[2:], key=lambda r: (r["neg_triggers"] - 0.5 * r["pos_right_n"], r["neg_dance_s"]))[:18]
for r in show:
  print(f"{r['name']:<40} {r['neg_triggers']:>7} {r['neg_dance_s']:>10} | {r['pos_right']:>8} {r['wrong']:>5} "
        f"{r['t_med']} | {r['neg_videos']} / {r['missed']}")
