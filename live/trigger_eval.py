"""Offline replica of the live recogniser + routine trigger (server.py, playback=routine) on pre-computed YOLO
keypoints (kp_live_tests.py), to compare trigger rules quickly on positive and negative videos.

Per 0.1 s tick (server: every 5 policy steps at 50 Hz): newest keypoints <= 0.5 s old, 1 s window resampled to 30
samples (KpBuffer.window), legs visible (mean conf of joints 11-16 >= 0.4) -> RetrieveNet -> (dance, frame, conf).
Routine logic as in server.py: trigger -> replay of the learned clip (its full length); a person-started replay
stops after stop_after s of "not doing it"; a new trigger needs min_idle s of standing.
Rules: base = one qualifying tick (moving state of a dance, conf >= trigger_conf; the live default);
hold = the last `hold` s of ticks all qualify for the same dance, the canonical frame does not run backwards by more
than `back` frames between ticks and advances >= `adv` x real time over the window, and the moving-state probability
mass of that dance (move_p) is >= `move_p` on every tick.
Usage (unitree_rl_mjlab env): python trigger_eval.py [--dump]
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import torch

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "vla"))
from data import normalise  # noqa: E402
from train_retrieve import CANON_PHASE, STATE_DANCE, STATE_FRAME, RetrieveNet  # noqa: E402

H = Path.home()
KP = H / "projects/dance/vla/kp_live"
OUT = H / "projects/dance/vla/trigger_eval"
DANCE_ZH = {0: "闪身步", 1: "狗熊哆嗦毛"}
STAND = {(0, 60.0), (0, 34.0), (1, 5.0), (1, 225.0)}
# ground truth: which dance each test video shows (None = negative; "?" = positive, dance not labelled)
TRUTH = {**{f"unseen_sss_{i}": {0} for i in (1, 2, 3)}, **{f"unseen_gxdsm_{i}": {1} for i in (1, 2, 3)},
         "gym_sss": {0}, "hoodie_sss": {0}, "bda_ming_gxdsm_a": {1}, "bda_ming_gxdsm_b": {1},
         "unseen_switch": {0, 1}, "switch_test": {0, 1}, "user_1": "?", **{f"neg_{i}": None for i in range(1, 60)}}


def segments(ph):
  out, i = [], 0
  while i < len(ph):
    if ph[i] != "stand":
      j = i
      while j < len(ph) and ph[j] != "stand":
        j += 1
      out.append((i, j - 1))
      i = j
    else:
      i += 1
  return out


SEGS = {d: segments(CANON_PHASE[DANCE_ZH[d]]) for d in (0, 1)}


def seg_of(d, f):
  for k, (s0, s1) in enumerate(SEGS[d]):
    if s0 <= f <= s1:
      return k
  return None


MOVING = np.array([seg_of(int(d), float(f)) is not None and (int(d), float(f)) not in STAND
                   for d, f in zip(STATE_DANCE, STATE_FRAME)])


def predict_video(net, dev, name, jitter_seed=None):
  """jitter_seed: emulate the live loop - ~13 % of frames dropped (client at ~26 fps), tick times off by a random
  phase and +-20 ms jitter."""
  z = np.load(KP / f"{name}.npz")
  kp, sent, fps = z["kp"], z["sent"].copy(), float(z["fps"])
  ts = np.arange(len(kp)) / fps
  tick_times = np.arange(0.1, len(kp) / fps + 1e-9, 0.1)
  if jitter_seed is not None:
    r = np.random.default_rng(jitter_seed)
    sent &= r.random(len(sent)) > 0.13
    tick_times = tick_times + r.uniform(0, 0.1) + r.uniform(-0.02, 0.02, len(tick_times))
  ticks = []
  for tick in tick_times:
    idx = np.where(sent & (ts <= tick + 1e-9))[0]
    if len(idx) < 2 or tick - ts[idx[-1]] > 0.5:
      ticks.append({"t": round(tick, 2), "vis": "nobody"})
      continue
    grid = np.linspace(tick - 1.0 + 1.0 / 30, tick, 30)
    win = np.empty((30, 17, 3), np.float32)
    for j in range(17):
      for c in range(3):
        win[:, j, c] = np.interp(grid, ts[idx], kp[idx, j, c])
    if float(win[:, 11:17, 2].mean()) < 0.4:
      ticks.append({"t": round(tick, 2), "vis": "legs"})
      continue
    with torch.no_grad():
      pr = net(torch.tensor(normalise(win).reshape(1, 30, -1), device=dev)).softmax(-1)[0].cpu().numpy()
    other = float(pr[len(STATE_DANCE):].sum())  # open-set model: extra "other" class (0 for the closed model)
    pr = pr[:len(STATE_DANCE)] / max(1e-9, 1.0 - other)
    pd = [float(pr[STATE_DANCE == d].sum()) for d in (0, 1)]
    d = int(np.argmax(pd))
    m = pr.copy()
    m[STATE_DANCE != d] = 0
    k = int(m.argmax())
    ticks.append({"t": round(tick, 2), "vis": "ok", "d": d, "f": float(STATE_FRAME[k]), "conf": pd[d],
                  "move_p": float(pr[(STATE_DANCE == d) & MOVING].sum()), "pk": float(pr[k]), "other": other})
  return ticks


def moving(tk):
  return tk["vis"] == "ok" and seg_of(tk["d"], tk["f"]) is not None and (tk["d"], tk["f"]) not in STAND


def simulate(ticks, rule, clip_s, stop_after=0.85, min_idle=0.2):
  """Returns the list of replays (start t, dance, end t, why it ended)."""
  dt = 0.1
  n_hold = max(1, int(round(rule.get("hold", 0.0) / dt)) + 1) if rule.get("hold", 0) > 0 else 1
  routine, not_doing, idle_t, replays, hist = None, 0.0, 10.0, [], []
  for tk in ticks:
    t = tk["t"]
    if routine is not None:
      d0, t0 = routine
      if t - t0 >= clip_s[d0]:
        replays[-1][2:] = [t, "finished"]
        routine, idle_t, hist = None, 0.0, []
      else:
        doing = moving(tk) and tk["d"] == d0 and tk.get("other", 0.0) < rule.get("other_stop", 1.01)
        not_doing = 0.0 if doing else not_doing + dt
        if not_doing >= stop_after - 1e-6:
          replays[-1][2:] = [t, "person stopped"]
          routine, idle_t, hist = None, 0.0, []
        continue
    idle_t += dt
    q = (moving(tk) and tk["conf"] >= rule["conf"] and tk.get("move_p", 1.0) >= rule.get("move_p", 0.0)
         and tk.get("other", 0.0) < rule.get("other", 1.01))
    if rule.get("vote"):
      # vote (time based, = server.py): over the ticks of the last `win` s, >= `frac` of them qualify, the qualifying
      # ones span >= `span` s, are all the same dance, and their canonical frame runs forward (no backward jump >
      # back frames, net advance >= adv x real time)
      hist = [h for h in hist + [(tk, q)] if t - h[0]["t"] <= rule["win"] + 1e-6]
      votes = [h for h, ok in hist if ok]
      if idle_t < min_idle or not q or len(votes) < 2 or len(votes) < rule["frac"] * len(hist) \
          or votes[-1]["t"] - votes[0]["t"] < rule["span"] - 1e-6 or len({h["d"] for h in votes}) > 1:
        continue
      fs, tt = [h["f"] for h in votes], [h["t"] for h in votes]
      if min(np.diff(fs)) < -rule.get("back", 1e9) or fs[-1] - fs[0] < rule.get("adv", 0.0) * 30 * (tt[-1] - tt[0]):
        continue
      # window veto: mean 'other' probability over all recognitions of the window (open-set recogniser)
      om = [h.get("other", 0.0) for h, _ in hist if h["vis"] == "ok"]
      if om and float(np.mean(om)) >= rule.get("other_mean", 1.01):
        continue
      routine, not_doing = (tk["d"], t), 0.0
      replays.append([t, tk["d"], None, "video ended"])
      continue
    hist = (hist + [tk])[-n_hold:] if q else []
    if idle_t < min_idle or not q or len(hist) < n_hold:
      continue
    if n_hold > 1:
      ds = {h["d"] for h in hist}
      fs = [h["f"] for h in hist]
      if len(ds) > 1 or min(np.diff(fs)) < -rule.get("back", 1e9) or \
          fs[-1] - fs[0] < rule.get("adv", 0.0) * 30 * (len(hist) - 1) * dt:
        continue
    routine, not_doing = (hist[-1]["d"], t), 0.0
    replays.append([t, hist[-1]["d"], None, "video ended"])
  if routine is not None:
    replays[-1][2] = ticks[-1]["t"]
  return replays


def score(preds, rule, clip_s):
  neg_trig, neg_clips, neg_dance_s, pos = 0, 0, 0.0, {}
  for name, ticks in preds.items():
    tr = TRUTH.get(name, "?")
    reps = simulate(ticks, rule, clip_s)
    if tr is None:
      pos[name] = {"n": len(reps), "first_t": reps[0][0] if reps else None,
                   "first_dance": DANCE_ZH[reps[0][1]] if reps else None, "right": None, "wrong_n": len(reps)}
      neg_trig += len(reps)
      neg_clips += bool(reps)
      neg_dance_s += sum(r[2] - r[0] for r in reps)
    else:
      first = reps[0] if reps else None
      pos[name] = {"n": len(reps), "first_t": first[0] if first else None,
                   "first_dance": DANCE_ZH[first[1]] if first else None,
                   "right": None if tr == "?" or not first else first[1] in tr,
                   "wrong_n": None if tr == "?" else sum(r[1] not in tr for r in reps)}
  return {"neg_triggers": neg_trig, "neg_clips_triggered": neg_clips, "neg_robot_dance_s": round(neg_dance_s, 1),
          "pos": pos}


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--watch", default="ret_lead0_s0")
  ap.add_argument("--motion", default=str(H / "projects/dance/multi/canon_v1.npz"))
  ap.add_argument("--dump", action="store_true", help="print every tick of every video")
  a = ap.parse_args()
  dev = "cuda:0" if torch.cuda.is_available() else "cpu"
  ws = torch.load(H / "projects/dance/vla/runs" / a.watch / "model.pt", weights_only=False, map_location=dev)
  if ws.get("open"):
    from train_retrieve_open import OpenNet
    net = OpenNet().to(dev).eval()
  else:
    net = RetrieveNet().to(dev).eval()
  net.load_state_dict(ws["model"])
  OUT = OUT / a.watch
  mf = np.load(a.motion)
  names = [str(x) for x in mf["clip_names"]]
  lens = {n: int((mf["clip_id"] == i).sum()) for i, n in enumerate(names)}
  clip_s = {0: (lens["bda_zhao_sss"] - 3) / 50, 1: (lens["bda2_gxdsm_full"] - 3) / 50}
  print(f"segments (30 fps) {SEGS}; replay length s {clip_s}")
  OUT.mkdir(parents=True, exist_ok=True)
  preds = {p.stem: predict_video(net, dev, p.stem) for p in sorted(KP.glob("*.npz"))}
  (OUT / "ticks.json").write_text(json.dumps(preds))
  if a.dump:
    for n, tks in preds.items():
      print(n, " ".join(f"{t['t']:.1f}:{t['vis'] if t['vis'] != 'ok' else str(t['d']) + '/' + str(int(t['f'])) + '/' + str(round(t['conf'], 2)) + '/' + str(round(t['move_p'], 2))}" for t in tks))
  rules = [{"name": "live (base, conf 0.7)", "conf": 0.7}]
  others = (1.01,) if not ws.get("open") else (0.3, 0.5, 0.7)
  for hold, conf, mp, adv, oth in itertools.product((0.0, 0.3, 0.5, 0.7), (0.7, 0.9), (0.0, 0.5, 0.7), (0.0, 0.3),
                                                     others):
    rules.append({"name": f"hold {hold} conf {conf} mp {mp} adv {adv} oth {oth}", "hold": hold, "conf": conf,
                  "move_p": mp, "adv": adv, "back": 6, "other": oth, "other_stop": oth})
  res = []
  for r in rules:
    s = score(preds, r, clip_s)
    pv = [v for k, v in s["pos"].items() if TRUTH.get(k, "?") not in ("?", None)]
    hit = sum(v["n"] > 0 for v in pv)
    right = sum(bool(v["right"]) for v in pv)
    wrong = sum(v["wrong_n"] for v in pv)
    lat = [v["first_t"] for v in pv if v["first_t"] is not None]
    res.append({**r, **{k: s[k] for k in ("neg_triggers", "neg_clips_triggered", "neg_robot_dance_s")},
                "pos_hit": f"{hit}/{len(pv)}", "pos_first_right": right, "pos_wrong_dance_replays": wrong,
                "pos_first_t_median": round(float(np.median(lat)), 2) if lat else None, "detail": s["pos"]})
  (OUT / "rules.json").write_text(json.dumps(res, ensure_ascii=False, indent=1))
  print(f"{'rule':<42} negTrig negClips negDance_s | posHit firstRight wrongReplays firstT_med")
  for r in res:
    print(f"{r['name']:<42} {r['neg_triggers']:>7} {r['neg_clips_triggered']:>8} {r['neg_robot_dance_s']:>10} | "
          f"{r['pos_hit']:>6} {r['pos_first_right']:>10} {r['pos_wrong_dance_replays']:>12} {r['pos_first_t_median']}")
  for r in [res[0]] + sorted(res[1:], key=lambda r: (r["neg_triggers"], -int(r["pos_hit"].split("/")[0]),
                                                     -r["pos_first_right"]))[:3]:
    print(f"per video [{r['name']}]:", json.dumps({k: (v["n"], v["first_t"], v["first_dance"])
                                                   for k, v in r["detail"].items()}, ensure_ascii=False))
