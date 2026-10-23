"""Summarise the trend of key training curves from an rsl_rl log (same numbers W&B shows).

Usage (any python): python watch.py <run> [--every 100]
Prints one row every N iterations: reward, episode length, tracking errors, termination counts, iteration time.
Flags: NaN, reward collapse (latest < 50% of best after it was positive), stalled run (log not updated > 5 min).
"""
import argparse
import math
import os
import re
import time

KEYS = {"rew": "Mean reward", "len": "Mean episode length", "body": "Metrics/motion/error_body_pos",
        "anc": "Metrics/motion/error_anchor_pos", "jpos": "Metrics/motion/error_joint_pos",
        "t_ee": "Episode_Termination/ee_body_pos", "t_ori": "Episode_Termination/anchor_ori",
        "t_pos": "Episode_Termination/anchor_pos", "std": "Mean action std", "vloss": "Mean value loss",
        "itime": "Iteration time"}

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("run")
    ap.add_argument("--every", type=int, default=100)
    a = ap.parse_args()
    path = os.path.expanduser(f"~/projects/dance_logs/train_{a.run}.log")
    text = open(path, encoding="utf-8", errors="ignore").read()
    blocks = re.split(r"Learning iteration\s+(\d+)/(\d+)", text)
    rows, total = [], None
    for i in range(1, len(blocks) - 2, 3):
        it, total, body = int(blocks[i]), int(blocks[i + 1]), blocks[i + 2]
        r = {"it": it}
        for k, name in KEYS.items():
            m = re.search(re.escape(name) + r":\s*([-\d.eE+naNinf]+)", body)
            r[k] = float(m.group(1)) if m else float("nan")
        rows.append(r)
    if not rows:
        raise SystemExit("no iterations yet")
    pick = [r for r in rows if r["it"] % a.every == 0] + [rows[-1]]
    print(f"{'it':>5} {'reward':>7} {'ep_len':>7} {'body_err':>8} {'anchor':>7} {'joint':>6} "
          f"{'term_ee':>8} {'term_ori':>8} {'term_pos':>8} {'act_std':>7} {'v_loss':>7}")
    for r in pick:
        print(f"{r['it']:5d} {r['rew']:7.2f} {r['len']:7.1f} {r['body']:8.4f} {r['anc']:7.4f} {r['jpos']:6.3f} "
              f"{r['t_ee']:8.1f} {r['t_ori']:8.1f} {r['t_pos']:8.1f} {r['std']:7.3f} {r['vloss']:7.4f}")
    last = rows[-1]
    best = max(rows, key=lambda r: r["rew"] if not math.isnan(r["rew"]) else -1e9)
    eta_h = (total - last["it"]) * last["itime"] / 3600
    print(f"progress {last['it']}/{total}, {last['itime']:.2f}s/it, ETA ~{eta_h:.1f} h; "
          f"best reward {best['rew']:.2f} @ {best['it']}; max episode length is 500 steps (10 s)")
    flags = []
    if any(math.isnan(last[k]) for k in ("rew", "vloss")):
        flags.append("NaN in reward/value loss")
    if best["rew"] > 0 and last["rew"] < 0.5 * best["rew"]:
        flags.append("reward collapsed below 50% of best")
    if time.time() - os.path.getmtime(path) > 300:
        flags.append("log not updated for >5 min (stalled or finished)")
    print("FLAGS: " + ("; ".join(flags) if flags else "none"))
