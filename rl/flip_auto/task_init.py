"""Harness step 0 for a new task: register it with its motion family, build its checklist from the reference
(library.init_task) - which also inherits the verified fixes promoted to its family / generic scope - and make sure
the hand-written lessons are in the library (library.seed_lessons).
Usage (unitree_rl_mjlab env): python task_init.py <dataset clip, e.g. backflip_3> [variant=ballistic] [family=aerial]"""
import sys
from pathlib import Path

import mujoco
import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import library as libm  # noqa: E402

H = Path.home()
clip = sys.argv[1]
var = sys.argv[2] if len(sys.argv) > 2 else "ballistic"
family = sys.argv[3] if len(sys.argv) > 3 else "aerial"
DS = H / "projects/dance/dataset" / clip
ref = np.load(DS / f"g1_{var}_50fps.npz")
labels = np.load(DS / "labels_50fps.npz")
m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
jn = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
bn = ["pelvis", "left_hip_roll_link", "left_knee_link", "left_ankle_roll_link", "right_hip_roll_link",
      "right_knee_link", "right_ankle_roll_link", "torso_link", "left_shoulder_roll_link", "left_elbow_link",
      "left_wrist_yaw_link", "right_shoulder_roll_link", "right_elbow_link", "right_wrist_yaw_link"]
lib = libm.load()
libm.seed_lessons(lib)
added = libm.init_task(lib, clip, family, ref, labels, jn, bn, origin=f"init:{clip}")
libm.save(lib)
priors = [c["id"] for c in added if str(c.get("origin", "")).startswith("prior:")]
print(f"{clip} (family {family}): +{len(added)} task checks, {len(priors)} inherited priors {priors[:8]}")
print("library:", libm.summary(lib))
