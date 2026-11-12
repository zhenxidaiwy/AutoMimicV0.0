"""Dataset manifest for the world model: every past tracking run -> (checkpoint, motion, sim context), read from the
run's own params/env.yaml (the motion it trained on). Per run two checkpoints: the first saved after warm start and
the last, so both weak (falling) and good policies are in the data. Smoke runs are skipped.
Usage: python manifest.py [--out manifest.json]"""
import argparse
import json
import re
from pathlib import Path

LOGS = Path.home() / "projects/dance/runs/logs/rsl_rl/g1_tracking"
GETUP = Path.home() / "projects/dance/runs/logs/rsl_rl/g1_recovery"
AUTO = Path.home() / "projects/dance_logs/auto"
# the five skills trained so far (user 2026-11-02): 闪身步, 狗熊哆嗦毛, 起立, 后空翻, 侧手翻
SKILL = {"bda_zhao_sss": "shanshenbu", "bda_ming_gxdsm_a": "gouxiong", "bda2_gxdsm_full": "gouxiong",
         "backflip_2": "backflip", "backflip_3": "backflip", "cartwheel_2": "cartwheel"}


def skill_of(motion):
  p = Path(motion)
  return SKILL.get(p.parent.name, p.parent.name) if p.parent.name != "multi" else "multi_" + p.stem


def getup_rows():
  """get-up harness rounds (task Dance-Recovery-G1-auto, knobs per round); no reference motion."""
  rows = []
  for run in sorted(GETUP.glob("*_auto_r*")):
    ckpts = sorted(run.glob("model_*.pt"), key=lambda p: int(p.stem.split("_")[1]))
    knobs = AUTO / run.name.split("_auto_")[1] / "knobs.json"  # r00 .. r08, r09_part1
    if not ckpts or not knobs.exists():
      continue
    for c in ([ckpts[-1]] if len(ckpts) == 1 else [ckpts[0], ckpts[-1]]):
      rows.append({"run": run.name, "ckpt": str(c), "motion": "", "skill": "getup",
                   "task": "Dance-Recovery-G1-auto", "getup_knobs": str(knobs), "hand_friction": 0.0,
                   "knee_limit": 120.0})
  return rows


def main(a):
  rows = getup_rows()
  for run in sorted(LOGS.iterdir()):
    if not run.is_dir() or "smoke" in run.name:
      continue
    env = run / "params/env.yaml"
    if not env.exists():
      continue
    m = re.search(r"motion_file:\s*(\S+)", env.read_text())
    if not m or not Path(m.group(1)).exists():
      continue
    ckpts = sorted(run.glob("model_*.pt"), key=lambda p: int(p.stem.split("_")[1]))
    if not ckpts:
      continue
    pick = [ckpts[-1]] if len(ckpts) == 1 else [ckpts[0], ckpts[-1]]
    motion = m.group(1)
    for c in pick:
      rows.append({"run": run.name, "ckpt": str(c), "motion": motion, "skill": skill_of(motion),
                   "task": "Unitree-G1-Tracking-No-State-Estimation",
                   "hand_friction": 0.6 if "cartwheel" in motion else 0.0, "knee_limit": 120.0})
  Path(a.out).write_text(json.dumps(rows, indent=1))
  by = {}
  for r in rows:
    by[r["skill"]] = by.get(r["skill"], 0) + 1
  print(json.dumps({"checkpoints": len(rows), "by_skill": by}))


if __name__ == "__main__":
  ap = argparse.ArgumentParser()
  ap.add_argument("--out", default=str(Path(__file__).resolve().parent / "manifest.json"))
  main(ap.parse_args())
