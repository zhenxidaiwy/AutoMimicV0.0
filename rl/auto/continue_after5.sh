#!/usr/bin/env bash
# After round 5 is recorded: stop the harness, re-measure rounds 4 and 5 with the current metrics.py (sway metrics),
# re-score both with the current harness.py (sway targets), continue from the better one with the current rules.
A=~/projects/dance_logs/auto; R=~/projects/dance/runs/logs/rsl_rl/g1_recovery
until [ -f $A/r05/metrics.json ] && grep -q '"round": 6' $A/state.json 2>/dev/null; do sleep 20; done
sleep 20
pkill -f "auto/resume.sh"; pkill -f "harness.py"; sleep 1; pkill -f "train_getup.py"; sleep 5
pgrep -fa "harness|train_getup" || echo "harness stopped"
for r in 04 05; do
  d=$A/r$r
  CK=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$d/metrics.json'))['ckpt'])")
  echo "re-measuring r$r: $CK"
  export GETUP_TASK=Dance-Recovery-G1-auto GETUP_KNOBS=$d/knobs.json
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $d/fall.json > $d/eval3.log 2>&1
  bash ~/dance_win/rl/auto/run_mjlab.sh python ~/dance_win/rl/auto/metrics.py --ckpt $CK --out $d/stand.json --stand_start >> $d/eval3.log 2>&1
done
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import json, math, sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "dance_win/rl/auto"))
import harness as h
A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
best = None
for r in (4, 5):
  d = A / f"r{r:02d}"
  m = json.loads((d / "fall.json").read_text()); m.update(json.loads((d / "stand.json").read_text()))
  m["t_stand_min_pose"] = min((v["t_stand"] for v in m["per_pose"].values() if not math.isnan(v["t_stand"])),
                              default=float("nan"))
  (d / "metrics.json").write_text(json.dumps(m, indent=1))
  sc = h.score(m)
  ok = sum(h.check(m, *spec) for spec in h.TARGETS.values())
  print(f"round {r}: rescored {sc:.2f}, targets {ok}/{len(h.TARGETS)}, sway {m['sway_pp_cm_median']:.1f} / "
        f"{m['stand_start_sway_pp_cm']:.1f} cm, foot travel {m['foot_travel_after_stand_median']:.2f} m, "
        f"squat {m['squat_match_median']:.2f}, t {m['t_stand_median']:.2f} s, success {m['success']:.2f}")
  if best is None or sc > best["score"]:
    best = {"round": r, "score": sc, "run": Path(m["ckpt"]).parent.name, "ckpt": m["ckpt"],
            "knobs": json.loads((d / "knobs.json").read_text())}
s["best"] = best
k, ch = h.adjust(best["knobs"], json.loads((A / f"r{best['round']:02d}" / "metrics.json").read_text()))
s.update(knobs=k, warm=best["run"], warm_ckpt=Path(best["ckpt"]).name, met_streak=0)
(A / "state.json").write_text(json.dumps(s, indent=1))
with open(h.REPORT, "a") as f:
  f.write(f"## Harness restarted after round 5 ({__import__('datetime').datetime.now():%Y-%m-%d %H:%M}): new "
          "targets for upper-body sway after standing (user saw a slow sway in auto_r04: measured 4.3 / 3.5 cm "
          "fore-aft / sideways p-p at ~0.7 Hz from a standing start) and new reward terms torso_still / arm_still; "
          f"rounds 4-5 re-measured, continuing from round {best['round']} (score {best['score']:.2f})\n\n"
          "- next round changes:\n" + "".join(f"  - {c}\n" for c in ch) + "\n")
print(f"continue from round {best['round']}; next round {s['round']} changes:"); print("\n".join(ch))
EOF
N=$(~/miniforge3/envs/gmr/bin/python -c "import json;print(json.load(open('$A/state.json'))['round'])")
for d in $R/*_auto_r$(printf "%02d" $N); do [ -d "$d" ] && rm -rf "$d" && echo "removed half-started $d"; done
rm -rf $A/r$(printf "%02d" $N)
cd ~/dance_win/rl/auto && exec ~/miniforge3/envs/gmr/bin/python -u harness.py --warm unused --rounds 10 --iters 1500
