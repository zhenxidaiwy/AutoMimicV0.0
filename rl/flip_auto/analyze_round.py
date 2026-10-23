"""Analysis pack for the LLM decider, one per round: best checkpoint's HD video, every-step frame sheets of the whole
clip (40 steps per sheet, frame index burnt in), the eval metrics vs. the previous round, and the critic summary.
Usage (unitree_rl_mjlab env): python analyze_round.py [round K, default = last evaluated]
Output: ~/dance_win/videos/backflip/auto/rK/ (video, sheets) + printed summary"""
import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = Path.home()
LOGS = H / "projects/dance/runs/logs/rsl_rl/g1_tracking"
KEYS = ["score", "robot_rotation_deg", "robot_airborne_s", "pelvis_rise_m", "landed_upright", "stand_stable",
        "early_fall", "plane_dev_max_deg", "leg_asym_deg", "feet_dist_max_m", "knee_sep_max_m", "hip_roll_max_rad",
        "hip_yaw_max_rad", "flight_hip_err_rad", "track_body_err_m", "track_joint_err", "stand_arm_vel_rms",
        "stand_action_change", "stand_pelvis_speed", "stand_torso_angvel", "takeoff_offset_steps",
        "landing_offset_steps"]

st = json.loads((HERE / "state.json").read_text())
k = int(sys.argv[1]) if len(sys.argv) > 1 else len(st["rounds"])
rd = st["rounds"][k - 1]
best = max(rd["evals"], key=lambda e: e.get("score", -1))
ck = best["ckpt"][:-3]
ev = LOGS / rd["run"] / "eval"
out = H / "dance_win/videos/backflip/auto" / f"r{k:02d}"
out.mkdir(parents=True, exist_ok=True)
vid = ev / f"flip_auto_{ck}.mp4"
dst = out / f"r{k:02d}_{ck}.mp4"
shutil.copy(vid, dst)
n = int(subprocess.run(["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0", "-show_entries",
                        "stream=nb_read_frames", "-of", "csv=p=0", str(dst)], capture_output=True, text=True).stdout)
for a in range(0, n, 40):
  b = min(a + 39, n - 1)
  subprocess.run(["bash", str(H / "dance_win/scripts/data/sheet_grid.sh"), str(dst), str(out / f"sheet_{a:03d}-{b:03d}.jpg"),
                  str(a), str(b), "1", "8"])
print(f"round {k}  run {rd['run']}  best {best['ckpt']}  video {dst}  ({n} frames, sheets every step in {out})")
# r08 lesson: the decider looked at sheets 80-187 only and skipped stand / crouch. Every sheet must be reviewed
# before the decision is written; the decision file lists them under "reviewed_sheets".
print("CHECKLIST - review every sheet before writing the decision:")
for a in range(0, n, 40):
  print(f"  [ ] {out / f'sheet_{a:03d}-{min(a + 39, n - 1):03d}.jpg'}")
prev = None
if k > 1:
  prev = max(st["rounds"][k - 2]["evals"], key=lambda e: e.get("score", -1))
print(f"{'metric':28s} {'r' + str(k):>10s} {'r' + str(k - 1):>10s}")
for key in KEYS:
  print(f"{key:28s} {str(best.get(key, '-')):>10s} {str(prev.get(key, '-')) if prev else '-':>10s}")
for e in rd["evals"]:
  print("  ckpt", e["ckpt"], "score", e.get("score"))
crit = ev / f"flip_auto_{ck}_critic.md"
if crit.exists():
  shutil.copy(crit, out / crit.name)
  print("".join(crit.read_text().splitlines(True)[:45]))
for w in rd.get("why", []):
  print("rule:", w)
for c in rd.get("library_changes", [])[:20]:
  print("library:", c)
