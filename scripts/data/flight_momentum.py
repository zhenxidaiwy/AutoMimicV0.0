"""Make the flight rotation of a backflip reference physically consistent: in the air the angular momentum is
conserved, so the pitch rate must follow omega(t) = L / I(t) (I = whole-body inertia about the flip axis for the pose
of that frame). The retimed reference had a spin spike (~35 deg per 50 Hz step, ~30 rad/s, vs ~8 rad/s before) that
no robot can follow. Here the rotation between the last ground frame (T-1) and the landing frame L keeps its start /
end orientation but is redistributed with d(phi)/dt proportional to 1 / I(t).
Input/output: data/g1/<clip>/g1_<variant>.csv (30 fps); writes g1_<variant>_mc.csv.
Usage (unitree_rl_mjlab env): python flight_momentum.py <clip> <variant> <T> <L>
"""
import sys
from pathlib import Path

import mujoco
import numpy as np
from scipy.spatial.transform import Rotation as R

H = Path.home()
clip, var, T, L = sys.argv[1], sys.argv[2], int(sys.argv[3]), int(sys.argv[4])
G = H / "projects/dance/data/g1" / clip
c = np.loadtxt(G / f"g1_{var}.csv", delimiter=",")
m = mujoco.MjModel.from_binary_path(str(H / "dance_win/sim2sim/models/dance.mjb"))
d = mujoco.MjData(m)
PELVIS = mujoco.mj_name2id(m, mujoco.mjtObj.mjOBJ_BODY, "robot/pelvis")

a, b = T - 1, L  # orientations kept at a (last ground frame) and b (first landing frame)
qa, qb = R.from_quat(c[a, 3:7]), R.from_quat(c[b, 3:7])
rel = (qa.inv() * qb).as_rotvec()  # body-frame rotation a -> b (if it exceeded 180 deg use the per-frame path)
inc = (R.from_quat(c[a:b, 3:7]).inv() * R.from_quat(c[a + 1:b + 1, 3:7])).as_rotvec()
axis_b = inc.sum(0)
total = np.linalg.norm(axis_b)
axis_b /= total
I = []
for f in range(a, b + 1):
  d.qpos[:3] = c[f, :3]
  d.qpos[3:7] = [1, 0, 0, 0]  # inertia about the body-frame flip axis does not depend on the root rotation
  d.qpos[7:7 + c.shape[1] - 7] = c[f, 7:]
  mujoco.mj_forward(m, d)
  com = d.subtree_com[PELVIS]
  Ia = 0.0
  for bi in range(PELVIS, m.nbody):
    Rb = d.ximat[bi].reshape(3, 3)
    r = d.xipos[bi] - com
    Ia += axis_b @ (Rb @ np.diag(m.body_inertia[bi]) @ Rb.T) @ axis_b + m.body_mass[bi] * (r @ r - (r @ axis_b) ** 2)
  I.append(Ia)
I = np.array(I)
w = 1.0 / I[:-1] + 1.0 / I[1:]  # trapezoid of 1/I per interval
phi = np.concatenate([[0.0], np.cumsum(w)]) / w.sum() * total  # cumulative angle at each frame a..b
old_phi = np.concatenate([[0.0], np.cumsum(np.linalg.norm(inc, axis=1))])
out = c.copy()
for k, f in enumerate(range(a, b + 1)):
  out[f, 3:7] = (qa * R.from_rotvec(axis_b * phi[k])).as_quat()
np.savetxt(G / f"g1_{var}_mc.csv", out.astype(np.float32), delimiter=",")
dphi_old = np.degrees(np.diff(old_phi)) * 30 / 50
dphi_new = np.degrees(np.diff(phi)) * 30 / 50
print(f"{clip}: flight frames {a}..{b}, total {np.degrees(total):.0f} deg, I {I.min():.2f}..{I.max():.2f} kg m2")
print("deg per 50 Hz step, old:", np.round(dphi_old, 0).tolist())
print("deg per 50 Hz step, new:", np.round(dphi_new, 0).tolist())
