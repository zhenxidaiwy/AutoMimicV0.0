"""Generic physics check: can the robot's PD actuators follow the reference joints at all?  Base held kinematically on
the reference root (no balance needed), position targets = reference joints, physics of the training model
(sim2sim/models/flip.mjb, 5 ms).  Reports per-joint tracking error and the largest contacts, so a joint that cannot
follow (collision, actuator sign / order, weak gain) shows up before any RL.
Usage (unitree_rl_mjlab env): python ref_pd_track.py <ref npz> [first last] [joint substring ...]"""
import sys
from pathlib import Path

import mujoco
import numpy as np

m = mujoco.MjModel.from_binary_path(str(Path(__file__).resolve().parents[2] / "sim2sim/models/flip.mjb"))
d = mujoco.MjData(m)
z = np.load(sys.argv[1])
a, b = (int(sys.argv[2]), int(sys.argv[3])) if len(sys.argv) > 3 else (0, 60)
filt = sys.argv[4:] or ["shoulder", "elbow"]
jn = [m.joint(i).name.replace("robot/", "") for i in range(1, m.njnt)]
act_q = [m.jnt_qposadr[m.actuator_trnid[i, 0]] - 7 for i in range(m.nu)]   # joint index (motion order) per actuator
sub = int(round(0.02 / m.opt.timestep))
d.qpos[:3], d.qpos[3:7], d.qpos[7:] = z["body_pos_w"][a, 0], z["body_quat_w"][a, 0], z["joint_pos"][a]
mujoco.mj_forward(m, d)
err = []
for t in range(a, b + 1):
  d.ctrl[:] = z["joint_pos"][t][act_q]
  for _ in range(sub):
    d.qpos[:3], d.qpos[3:7], d.qvel[:6] = z["body_pos_w"][t, 0], z["body_quat_w"][t, 0], 0.0
    mujoco.mj_step(m, d)
  err.append(d.qpos[7:] - z["joint_pos"][min(t + 1, len(z["joint_pos"]) - 1)])
err = np.array(err)
print(f"frames {a}-{b}, base held on the reference; |robot - reference| (rad) mean / max per joint:")
for i, n in enumerate(jn):
  if any(f in n for f in filt):
    print(f"  {n:28s} {np.abs(err[:, i]).mean():.3f} / {np.abs(err[:, i]).max():.3f}   end robot {d.qpos[7 + i]:+.2f} ref "
          f"{z['joint_pos'][b, i]:+.2f}")
print("worst joints:", ", ".join(f"{jn[i]} {np.abs(err[:, i]).max():.2f}" for i in np.argsort(-np.abs(err).max(0))[:5]))
print("actuator -> joint order identical:", act_q == list(range(m.nu)))
