"""Harness step 0 for a new task: build the initial checklist from the reference (library.init_from_reference) and
register the hand-written fixes found so far (library.seed_custom).
Usage (unitree_rl_mjlab env): python task_init.py <dataset clip, e.g. backflip_3> [variant=ballistic]"""
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library as libm  # noqa: E402

H = Path.home()
clip = sys.argv[1]
var = sys.argv[2] if len(sys.argv) > 2 else "ballistic"
DS = H / "projects/dance/dataset" / clip
ref = np.load(DS / f"g1_{var}_50fps.npz")
labels = np.load(DS / "labels_50fps.npz")
m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
jn = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
bn = ["pelvis", "left_hip_roll_link", "left_knee_link", "left_ankle_roll_link", "right_hip_roll_link",
      "right_knee_link", "right_ankle_roll_link", "torso_link", "left_shoulder_roll_link", "left_elbow_link",
      "left_wrist_yaw_link", "right_shoulder_roll_link", "right_elbow_link", "right_wrist_yaw_link"]
lib = libm.load()
added = libm.init_from_reference(lib, ref, labels, jn, bn, origin=f"init:{clip}")
libm.seed_custom(lib)
libm.save(lib)
kinds = {}
for c in lib["checks"]:
  kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
print(f"{clip}: +{len(added)} checks from the reference; library now {len(lib['checks'])} checks: {kinds}")
