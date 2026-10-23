#!/usr/bin/env bash
# After harness round K is recorded: stop the harness, re-measure every finished round with the current metrics.py,
# re-score with the current harness.py (new targets), pick the best, recompute the next knobs, restart the harness.
# Usage: bash continue_after.sh K
K=$(printf "%02d" $1); A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
until [ -f $A/r$K/metrics.json ] && grep -q "\"round\": $(( $1 + 1 ))" $A/state.json 2>/dev/null; do sleep 20; done
sleep 30
pkill -f "continue_after_r0.sh"; pkill -f "auto/start.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
pgrep -fa "harness|train_getup" || echo "harness stopped"
for d in $A/r[0-9][0-9]; do
  r=$(basename $d)
  [ -f $d/metrics.json ] || continue
  CK=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$d/metrics.json'))['ckpt'])")
  echo "re-measuring $r: $CK"
  export GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$d/knobs.json
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $d/fall.json > $d/eval2.log 2>&1
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $d/stand.json --stand_start >> $d/eval2.log 2>&1
done
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "dance_win/rl/auto"))
import harness as h
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
best = None
for d in sorted(A.glob("r[0-9][0-9]")):
  if not (d / "metrics.json").exists():
    continue
  m = json.loads((d / "fall.json").read_text()); m.update(json.loads((d / "stand.json").read_text()))
  m["t_stand_min_pose"] = min((v["t_stand"] for v in m["per_pose"].values() if not math.isnan(v["t_stand"])),
                              default=float("nan"))
  (d / "metrics.json").write_text(json.dumps(m, indent=1))
  sc = h.score(m)
  r = int(d.name[1:])
  run = Path(m["ckpt"]).parent.name
  knobs = json.loads((d / "knobs.json").read_text())
  ok = sum(h.check(m, *spec) for spec in h.TARGETS.values())
  print(f"round {r}: rescored {sc:.2f}, targets {ok}/{len(h.TARGETS)}; feet travel after standing "
        f"{m['foot_travel_after_stand_median']:.2f} m, touchdowns rising {m['touchdowns_rising_median']:.1f}, "
        f"peak force {m['peak_foot_force_median']:.0f} N, squat {m['squat_match_median']:.2f}, "
        f"t {m['t_stand_median']:.2f} s, success {m['success']:.2f}")
  if best is None or sc > best["score"]:
    best = {"round": r, "score": sc, "run": run, "ckpt": m["ckpt"], "knobs": knobs}
s["best"] = best
k, ch = h.adjust(best["knobs"], json.loads((A / f"r{best['round']:02d}" / "metrics.json").read_text()))
s["knobs"], s["warm"], s["met_streak"] = k, best["run"], 0
s["warm_ckpt"] = Path(best["ckpt"]).name
(A / "state.json").write_text(json.dumps(s, indent=1))
with open(h.REPORT, "a") as f:
  f.write(f"## Harness restarted ({__import__('datetime').datetime.now():%Y-%m-%d %H:%M}): new targets "
          f"(no stomping / balance stepping), all rounds re-measured; best = round {best['round']} "
          f"(score {best['score']:.2f})\n\n- next round changes:\n" + "".join(f"  - {c}\n" for c in ch) + "\n")
print(f"best round {best['round']}, next round {s['round']} knobs changes:"); print("\n".join(ch))
EOF
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
for d in $R/*_auto_r$(printf "%02d" $N); do [ -d "$d" ] && rm -rf "$d" && echo "removed half-started $d"; done
rm -rf $A/r$(printf "%02d" $N)
cd ~/dance_win/rl/auto && exec ~/miniforge3/envs/gmr/bin/python -u harness.py --warm unused --rounds 10 --iters 1500
