"""Manual decision after the round-4 crash (KeyError while computing the next knobs; state.json not written):
record round 4 and continue from it instead of reverting to round 2 - round 2 was trained under the reward with
the 0.2 m feet-spread cliff (continuing it collapsed in round 3), and round 4's lower score comes from stepping,
which the new push-grace gate targets. Next knobs = rules applied to round 4's metrics."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as h  # noqa: E402

A = Path.home() / "projects/dance_logs/auto"
s = json.loads((A / "state.json").read_text())
m = json.loads((A / "r04" / "metrics.json").read_text())
k4 = json.loads((A / "r04" / "knobs.json").read_text())
sc = h.score(m)
s["best"] = {"round": 4, "score": sc, "run": Path(m["ckpt"]).parent.name, "ckpt": m["ckpt"], "knobs": k4}
k, ch = h.adjust(k4, m)
s.update(knobs=k, warm=s["best"]["run"], warm_ckpt=Path(m["ckpt"]).name, round=5, met_streak=0)
(A / "state.json").write_text(json.dumps(s, indent=1))
with open(h.REPORT, "a") as f:
  f.write("## Manual decision after round 4 (2026-10-21 13:50)\n\n"
          f"- harness crashed computing round 5 knobs (KeyError for a knob added mid-run; fixed).\n"
          f"- round 4 (score {sc:.2f}) is taken as the base instead of round 2 (8.23): round 2 was trained with the "
          "0.2 m feet-spread cliff and collapsed when continued; round 4 has the best stance so far (torso 0.7 deg, "
          "template 0.95) and loses points only on stepping (foot travel 0.11 m, 5 touchdowns while rising).\n"
          "- stepping fix: the no-stepping penalty is now off only within 1 s after a training push (push_grace), "
          "instead of the leaky pelvis-speed gate.\n- next round changes:\n" + "".join(f"  - {c}\n" for c in ch) + "\n")
print("round 5 from", s["warm"], s["warm_ckpt"]); print("\n".join(ch))
