"""Reference knee / hip-pitch angles at stand, crouch bottom, mid-flight (tuck) and landing: checks flexion signs."""
from pathlib import Path

import mujoco
import numpy as np

H = Path.home()
m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
names = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
z = np.load(H / "projects/dance/dataset/backflip_3/g1_ballistic_50fps.npz")
lab = np.load(H / "projects/dance/dataset/backflip_3/labels_50fps.npz")
pn = [str(x) for x in lab["phase_names"]]
fl = np.where(lab["phase"] == pn.index("flight"))[0]
ld = np.where(lab["phase"] == pn.index("land"))[0]
cr = np.where(lab["phase"] == pn.index("crouch"))[0]
frames = {"stand": 5, "crouch_end": int(cr[-1]), "mid_flight": int(fl[len(fl) // 2]), "land+5": int(ld[0]) + 5}
for j in ("left_knee_joint", "left_hip_pitch_joint", "right_knee_joint", "right_hip_pitch_joint"):
  i = names.index(j)
  rng = m.jnt_range[i + 1]
  print(j, "range", np.round(rng, 2), {k: round(float(z["joint_pos"][f, i]), 2) for k, f in frames.items()})
print("flight frames", fl[0], fl[-1], "land", ld[0])
