"""Task registry of the harness: which clip / reference / family a run works on and where its state, decisions,
analyses, videos and logs live. Selected by the environment variable AUTOMIMIC_TASK (default backflip_3, whose paths
are the historical ones so its rounds 1-16 stay valid). Every harness script imports this module.
Add a task: an entry in TASKS (clip = dataset/<clip>, variant = g1_<variant>_50fps.npz, labels = labels file)."""
import os
from pathlib import Path

HERE = Path(__file__).resolve().parent
H = Path.home()
TASKS = {
  "backflip_3": {"variant": "ballistic", "labels": "labels_50fps.npz", "family": "aerial",
                 "root": HERE, "vid": H / "dance_win/videos/backflip/auto", "run_prefix": "flipauto"},
  # cartwheel (user-chosen source csf2.mp4, 2026-10-25): first evaluation-style skill of the hand_support family
  "cartwheel_2": {"variant": "lock_vlm_hold", "labels": "labels_hold_50fps.npz", "family": "hand_support",
                  "root": HERE / "tasks/cartwheel_2", "vid": H / "dance_win/videos/cartwheel_2/auto",
                  "run_prefix": "cw2auto"},
  # the same clip with the world-model inner trainer (rl/wm/speedup/online.py, harness --trainer wm): own state,
  # decisions, videos and run names; dataset and library entries are the clip's ("clip")
  "cartwheel_2_wm": {"clip": "cartwheel_2", "variant": "lock_vlm_hold", "labels": "labels_hold_50fps.npz",
                     "family": "hand_support", "root": HERE / "tasks/cartwheel_2_wm",
                     "vid": H / "dance_win/videos/cartwheel_2_wm/auto", "run_prefix": "cw2wm"},
}
TASK = os.environ.get("AUTOMIMIC_TASK", "backflip_3")
T = TASKS[TASK]
CLIP, VAR, LABELS, FAMILY = T.get("clip", TASK), T["variant"], T["labels"], T["family"]
ROOT = Path(T["root"])
STATE = ROOT / "state.json"
DECISIONS = ROOT / "decisions"
ANALYSIS = ROOT / "analysis"
REPORT = ROOT / "REPORT.md"
VID = Path(T["vid"])
RUN_PREFIX = T["run_prefix"]
DS = H / "projects/dance/dataset" / CLIP
DL = H / "projects/dance_logs"
for p in (ROOT, DECISIONS, ANALYSIS, VID):
  p.mkdir(parents=True, exist_ok=True)


def run_name(rnd):
  return f"{RUN_PREFIX}_r{rnd:02d}"


def train_log(rnd):
  return DL / f"train_{run_name(rnd)}.log"
