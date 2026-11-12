"""Stance geometry of chosen frames of a G1 csv: per foot sole z (cm), ankle z, knee angle, hip-to-ankle distance vs
the fully straight leg length, pelvis z and tilt.  Usage (gmr env): python stance_check.py <csv> frame ..."""
import sys

import mujoco
import numpy as np

from ground_fix import FEET, XML, sole_heights

m = mujoco.MjModel.from_xml_path(XML)
d = mujoco.MjData(m)
c = np.loadtxt(sys.argv[1], delimiter=",")
qp = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)
hip = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f"{s}_hip_pitch_link") for s in ("left", "right")]
ank = [mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, f) for f in FEET]
kn = [m.jnt_qposadr[mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_JOINT, f"{s}_knee_joint")] for s in ("left", "right")]
q0 = np.zeros(m.nq)
q0[2], q0[3] = 1.0, 1.0
d.qpos[:] = q0
mujoco.mj_kinematics(m, d)
L = np.linalg.norm(d.xpos[hip[0]] - d.xpos[ank[0]])
print(f"straight leg hip->ankle {L:.3f} m; knee range {m.jnt_range[m.jnt_qposadr.tolist().index(kn[0])]}")
for t in map(int, sys.argv[2:]):
  d.qpos[:] = qp[t]
  mujoco.mj_kinematics(m, d)
  s = sole_heights(m, qp[t][None])[0][0]
  tilt = np.degrees(np.arccos(np.clip(d.xmat[1].reshape(3, 3)[2, 2], -1, 1)))
  print(f"f{t}: pelvis z {qp[t, 2]:.3f} tilt {tilt:.1f} | " + " | ".join(
    f"{'LR'[j]}: sole {s[j] * 100:5.1f} cm, knee {qp[t, kn[j]]:+.2f}, reach {np.linalg.norm(d.xpos[hip[j]] - d.xpos[ank[j]]):.3f}"
    for j in range(2)))
