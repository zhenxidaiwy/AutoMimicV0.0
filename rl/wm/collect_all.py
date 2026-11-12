"""P1 data collection: a skill-balanced subset of the manifest, one collect.py process per checkpoint with a random
known sim context (foot friction, PD stiffness scale). Resumable (existing outputs are skipped); a checkpoint that
fails to load (e.g. an old observation layout) is logged and skipped.
Usage (unitree_rl_mjlab env): python collect_all.py [--per-skill 16] [--envs 512] [--steps 200] [--dry]"""
import argparse
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = Path.home() / "projects/dance/wm_data/v1"
# caps: every skill represented; the backflip's 58 checkpoints do not dominate
CAPS = {"backflip": 16, "cartwheel": 16, "getup": 14, "shanshenbu": 3, "gouxiong": 4, "multi_train_v1": 6,
        "multi_canon_v1": 2}


def pick(rows, scale):
  by = {}
  for r in rows:
    by.setdefault(r["skill"], []).append(r)
  sel = []
  for sk, rs in sorted(by.items()):
    cap = max(1, round(CAPS.get(sk, 4) * scale))
    if len(rs) > cap:  # spread over the history: evenly spaced, so early (weak) and late (good) policies are both in
      step = len(rs) / cap
      rs = [rs[int(i * step)] for i in range(cap)]
    sel += rs
  return sel


def main(a):
  rng = random.Random(0)
  rows = json.loads((HERE / "manifest.json").read_text())
  sel = pick(rows, a.scale)
  OUT.mkdir(parents=True, exist_ok=True)
  log = OUT / "collect_log.jsonl"
  print(json.dumps({"selected": len(sel), "by_skill": {s: sum(r["skill"] == s for r in sel) for s in CAPS}}))
  if a.dry:
    return
  for i, r in enumerate(sel):
    name = f"{r['skill']}__{r['run']}__{Path(r['ckpt']).stem}.npz"
    out = OUT / name
    if out.exists():
      continue
    fr = round(rng.uniform(0.4, 1.2), 2)
    kp = rng.choice([0.85, 1.0, 1.0, 1.1])
    cmd = [sys.executable, str(HERE / "collect.py"), "--ckpt", r["ckpt"], "--out", str(out), "--task", r["task"],
           "--envs", str(a.envs), "--steps", str(a.steps), "--friction", str(fr), "--kp-scale", str(kp),
           "--hand-friction", str(r["hand_friction"]), "--knee-limit", str(r["knee_limit"]), "--seed", str(i)]
    if r["motion"]:
      cmd += ["--motion", r["motion"]]
    env = dict(os.environ)
    if r.get("getup_knobs"):
      env.update(GETUP_TASK=r["task"], GETUP_KNOBS=r["getup_knobs"])
    t0 = time.time()
    p = subprocess.run(cmd, capture_output=True, text=True, env=env)
    rec = {"i": i, "out": name, "ok": p.returncode == 0, "min": round((time.time() - t0) / 60, 2),
           "friction": fr, "kp_scale": kp}
    if p.returncode != 0:
      rec["err"] = p.stderr.strip().splitlines()[-1][:300] if p.stderr.strip() else "?"
    else:
      rec.update(json.loads(p.stdout.strip().splitlines()[-1]))
    with log.open("a") as f:
      f.write(json.dumps(rec) + "\n")
    print(json.dumps(rec), flush=True)


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--scale", type=float, default=1.0, help="multiplies the per-skill caps")
  ap.add_argument("--envs", type=int, default=512)
  ap.add_argument("--steps", type=int, default=200)
  ap.add_argument("--dry", action="store_true")
  main(ap.parse_args())
