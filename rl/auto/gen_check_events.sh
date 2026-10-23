#!/usr/bin/env bash
# (1) Which randomisation events exist in the play config (did the friction / CoM conditions actually change
# anything?), (2) contact sheet of the generalisation video.
GETUP_TASK=Dance-Recovery-G1-v7f bash ~/dance_win/rl/auto/run_mjlab.sh python - <<'EOF' 2>&1 | grep -E "^EV"
import sys
from pathlib import Path
sys.path.insert(0, str(Path.home() / "projects/unitree_rl_mjlab")); sys.path.insert(0, str(Path.home() / "dance_win/rl"))
import mjlab.tasks  # noqa
from getup import TASK_ID
from mjlab.tasks.registry import load_env_cfg
cfg = load_env_cfg(TASK_ID, play=True)
for k, e in cfg.events.items():
  print("EV", k, e.mode, {kk: vv for kk, vv in e.params.items() if kk in ("ranges", "operation")},
        getattr(e.params.get("asset_cfg"), "geom_names", None), getattr(e.params.get("asset_cfg"), "body_names", None))
EOF
V=~/dance_win/videos/getup/getup_v7f_19500_generalization.mp4
~/miniforge3/envs/gmr/bin/python ~/dance_win/scripts/data/sheet.py $V ${V%.mp4}_sheet.png --every 1.5 --cols 2 --w 1440 --max_tiles 6
