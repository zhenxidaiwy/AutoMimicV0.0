"""Side-by-side metrics of harness rounds with per-target status. Usage: python compare_rounds.py 2 4"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import harness as h  # noqa: E402

A = Path.home() / "projects/dance_logs/auto"
rounds = [int(x) for x in sys.argv[1:]]
def load(r):
  d = A / f"r{r:02d}"
  if (d / "metrics.json").exists():
    return json.loads((d / "metrics.json").read_text())
  m = json.loads((d / "fall.json").read_text())  # round still rendering its video
  m.update(json.loads((d / "stand.json").read_text()))
  m["t_stand_min_pose"] = min(v["t_stand"] for v in m["per_pose"].values())
  return m


ms = {r: load(r) for r in rounds}
keys = ["success", "t_stand_median", "t_stand_min_pose", "feet_spread_median", "squat_match_median",
        "peak_joint_speed_median", "torso_tilt_median", "pelvis_tilt_median", "template_median",
        "stand_start_template", "foot_travel_after_stand_median", "touchdowns_rising_median",
        "touchdowns_after_stand_median", "peak_foot_force_median", "stand_start_foot_travel",
        "sway_pp_cm_median", "stand_start_sway_pp_cm", "torso_angv_rms_median"]
print(f"{'metric':<34}" + "".join(f"{'r' + str(r):>10}" for r in rounds))
for k in keys:
  print(f"{k:<34}" + "".join(f"{ms[r].get(k, float('nan')):>10.3f}" for r in rounds))
print(f"{'score':<34}" + "".join(f"{h.score(ms[r]):>10.2f}" for r in rounds))
for r in rounds:
  print(f"r{r} per pose:", {k: (round(v['t_stand'], 2), round(v['success'], 2)) for k, v in ms[r]['per_pose'].items()})
  print(f"r{r} failed targets:", [n for n, s in h.TARGETS.items() if not h.check(ms[r], *s)])
