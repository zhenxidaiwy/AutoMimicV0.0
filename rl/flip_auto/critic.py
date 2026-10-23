"""Automatic critic, library-driven (paper Fig. 1b-c). Compares the rollout with the reference from many angles,
evaluates every check of the diagnostic library, and reports deviations that NO check covers yet (new findings the
harness turns into new checks). Template fixes that do not help for 2 rounds are flagged for a hand-written fix.

Angles, per phase (stand frames after the reference landing = 'stand_after'), left/right merged per joint base:
  joint (mean |q - q_ref|), body (relative-frame position error), jitter (joint-acceleration RMS / reference),
  asymmetry (left/right difference beyond the reference's own), contact (foot up while the reference stands on it),
  timing (median per-joint lag, + = robot late).
Input : eval_flip.py <tag>_record.npz, labels_50fps.npz, [video], [--library]  Output: <tag>_critic.md/.json (+ jpg)
Usage : python critic.py <record.npz> <labels.npz> [video.mp4] [--round K] [--no-library]
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library as libm  # noqa: E402


def measure(R, L):
  jn = [str(x) for x in R["joint_names"]]
  bn = [str(x) for x in R["body_names"]]
  q, qr, act, bp, bpr, fz = R["q"], R["qr"], R["act"], R["bp"], R["bpr"], R["foot_z"]
  dt = float(R["dt"])
  T = len(q)
  names = libm.phase_names({"phase_names": L["phase_names"], "phase": L["phase"][:T]})
  phases = {p: np.array([i for i in range(T) if names[i] == p]) for p in dict.fromkeys(names)}
  V = {}  # (kind, target, phase) -> (value, tol, frames, detail)

  def put(kind, target, phase, value, frames, detail):
    tol = libm.TOL[kind]
    old = V.get((kind, target, phase))
    if old is None or value > old[0]:
      V[(kind, target, phase)] = (float(value), tol, [int(f) for f in frames], detail)

  acc = np.diff(q, 2, axis=0) / dt ** 2
  accr = np.diff(qr, 2, axis=0) / dt ** 2
  dact = np.abs(np.diff(act, axis=0)).mean(-1)
  for p, ii in phases.items():
    if len(ii) < 3:
      continue
    e = q[ii] - qr[ii]
    for j, n in enumerate(jn):
      k = int(np.argmax(np.abs(e[:, j])))
      put("joint", libm.base_of(n), p, np.abs(e[:, j]).mean(), [ii[k]],
          f"{n}: mean |err| {np.degrees(np.abs(e[:, j]).mean()):.0f} deg (signed {np.degrees(e[:, j].mean()):+.0f}), "
          f"step {ii[k]}: robot {q[ii[k], j]:+.2f} vs ref {qr[ii[k], j]:+.2f} rad")
    d = np.linalg.norm(bp[ii] - bpr[ii], axis=-1)
    for b, n in enumerate(bn):
      k = int(np.argmax(d[:, b]))
      put("body", libm.base_of(n), p, d[:, b].mean(), [ii[k]], f"{n}: mean {d[:, b].mean():.2f} m, max {d[k, b]:.2f} m")
    ii2 = ii[(ii >= 1) & (ii < T - 1)] - 1
    if len(ii2) >= 5:
      ra = np.sqrt((acc[ii2] ** 2).mean(0))
      rr = np.sqrt((accr[ii2] ** 2).mean(0)) + 5.0
      for j, n in enumerate(jn):
        put("jitter", libm.base_of(n), p, ra[j] / rr[j] * 1.0, [ii2[0] + 1],
            f"{n}: joint acceleration RMS {ra[j]:.0f} vs reference {rr[j] - 5:.0f} rad/s^2")
      if p in ("settle", "stand_after"):
        m = dact[np.clip(ii - 1, 0, len(dact) - 1)].mean()
        put("jitter", "all", p, m / 0.05 * libm.TOL["jitter"], [ii[0]], f"mean action change {m:.3f} (quiet < 0.05)")
    for base, s in libm.PAIRS.items():
      li, ri = f"left_{base}_joint", f"right_{base}_joint"
      if li not in jn:
        continue
      a = np.abs(q[ii, jn.index(ri)] - s * q[ii, jn.index(li)])
      ar = np.abs(qr[ii, jn.index(ri)] - s * qr[ii, jn.index(li)])
      k = int(np.argmax(a - ar))
      put("asymmetry", base, p, (a - ar).mean(), [ii[k]],
          f"left/right differ {np.degrees(a.mean()):.0f} deg vs reference {np.degrees(ar.mean()):.0f} deg")
    if p in ("crouch", "land", "settle", "stand_after", "stand"):
      for f, side in ((0, "left_foot"), (1, "right_foot")):
        bad = ii[fz[ii, f] > 0.06]
        put("contact", side, p, float(len(bad)), bad[:1] if len(bad) else [ii[0]],
            f"{side} off the floor for {len(bad)} of {len(ii)} steps")
  dyn = np.array([i for i in range(T) if names[i] in ("crouch", "takeoff", "flight", "land")])
  if len(dyn) > 20:
    lags = []
    for j in range(len(jn)):
      x, y = q[dyn, j] - q[dyn, j].mean(), qr[dyn, j] - qr[dyn, j].mean()
      if y.std() >= 0.05:
        lags.append((jn[j], max(range(-10, 11), key=lambda s: np.dot(np.roll(x, -s), y))))
    if lags:
      med = float(np.median([l for _, l in lags]))
      put("timing", "whole_body", "crouch..land", abs(med), [int(dyn[0])],
          f"median per-joint lag {med:+.0f} steps (+ late, - early); "
          + ", ".join(f"{n.replace('_joint', '')} {l:+d}" for n, l in sorted(lags, key=lambda t: -abs(t[1]))[:5]))
  return V


def main():
  args = [a for a in sys.argv[1:] if not a.startswith("--")]
  rnd = int(sys.argv[sys.argv.index("--round") + 1]) if "--round" in sys.argv else None
  if rnd is not None:
    args = [a for a in args if a != str(rnd)]
  if "--task" in sys.argv:
    args = [a for a in args if a != sys.argv[sys.argv.index("--task") + 1]]
  rec_p, lab_p = Path(args[0]), Path(args[1])
  video = Path(args[2]) if len(args) > 2 else None
  R = np.load(rec_p, allow_pickle=True)
  V = measure(R, np.load(lab_p))
  rows = sorted(({"kind": k, "what": t, "phase": p, "value": round(v, 4), "severity": round(v / tol, 2),
                  "frames": fr, "detail": d} for (k, t, p), (v, tol, fr, d) in V.items()), key=lambda r: -r["severity"])
  out = {"issues": [r for r in rows if r["severity"] > 1]}
  if "--no-library" not in sys.argv:
    lib = libm.load()
    task = sys.argv[sys.argv.index("--task") + 1] if "--task" in sys.argv else next(iter(lib.get("tasks", {})), None)
    covered = set()
    status = []
    for c in libm.task_checks(lib, task):  # measured checks live in the task scope (priors were copied there)
      key = (c["kind"], c["target"], c["phase"])
      if key in V:
        v, tol, fr, d = V[key]
        sev = round(v / tol, 2)
        covered.add(key)
        c.setdefault("history", []).append({"round": rnd, "value": round(v, 4), "severity": sev,
                                            "weight": c.get("weight", 0.0)})
        status.append({"id": c["id"], "severity": sev, "pass": sev <= 1, "weight": c.get("weight", 0),
                       "escalate": libm.stagnating(c), "detail": d})
    out["checks"] = sorted(status, key=lambda s: -s["severity"])
    out["new"] = [r for r in out["issues"] if (r["kind"], r["what"], r["phase"]) not in covered and r["severity"] > 2]
    out["task"] = task
    out["verified_now"] = libm.mark_verified(lib, task)
    libm.save(lib)
  out_json = rec_p.with_name(rec_p.name.replace("_record.npz", "_critic.json"))
  out_json.write_text(json.dumps(out, indent=1))
  md = ["# Automatic critic", "", f"{len(out['issues'])} deviations beyond tolerance", ""]
  if "checks" in out:
    fails = [s for s in out["checks"] if not s["pass"]]
    md += [f"## Library checks: {len(out['checks']) - len(fails)} pass, {len(fails)} fail", "",
           "| severity | check | fix weight | escalate | detail |", "|---|---|---|---|---|"]
    md += [f"| {s['severity']} | {s['id']} | {s['weight']} | {'YES' if s['escalate'] else ''} | {s['detail']} |"
           for s in fails[:25]]
    md += ["", f"## New findings (not covered by any check): {len(out['new'])}", "",
           "| severity | kind | what | phase | detail |", "|---|---|---|---|---|"]
    md += [f"| {r['severity']} | {r['kind']} | {r['what']} | {r['phase']} | {r['detail']} |" for r in out["new"][:25]]
  md += ["", "## All deviations (top 30)", "", "| severity | kind | what | phase | detail |", "|---|---|---|---|---|"]
  md += [f"| {r['severity']} | {r['kind']} | {r['what']} | {r['phase']} | {r['detail']} |" for r in out["issues"][:30]]
  out_json.with_suffix(".md").write_text("\n".join(md) + "\n")
  print("\n".join(md[:40]))
  if video and video.exists():
    frames = sorted({r["frames"][0] for r in out["issues"][:8] if r["frames"]})
    if frames:
      sel = "+".join(f"eq(n\\,{f})" for f in frames)
      sheet = out_json.with_name(out_json.stem + "_worst.jpg")
      subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-i", str(video), "-vf",
                      f"drawtext=text='%{{n}}':x=8:y=8:fontsize=44:fontcolor=yellow:box=1:boxcolor=black@0.6,"
                      f"select='{sel}',scale=-2:360,tile={len(frames)}x1", "-frames:v", "1", str(sheet)])
      print("worst frames:", frames, "->", sheet)


if __name__ == "__main__":
  main()
