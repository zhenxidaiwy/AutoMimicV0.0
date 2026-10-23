"""Which actuators are force-saturated in the native get-up closed loop (out/getup_native.npz), by phase?
Saturation is evaluated at the start of each policy step: state after step s-1, ctrl from the action of step s.
-> out/getup_satnames.json"""
import json
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from native_getup import OUT, NativeG1  # noqa: E402

import mujoco  # noqa: E402

nat = NativeG1()
m, d = nat.m, nat.d
lg = np.load(OUT / "getup_native.npz")
ref = np.load(OUT / "getup_mjlab.npz")
q, v, a = lg["qpos"], lg["qvel"], lg["act"]
T, n = a.shape[0], a.shape[1]
G, B0, B1, B2 = m.actuator_gainprm[:, 0], m.actuator_biasprm[:, 0], m.actuator_biasprm[:, 1], m.actuator_biasprm[:, 2]
FR = m.actuator_forcerange
names = [m.actuator(i).name.split("/")[-1] for i in range(m.nu)]
sat = np.zeros((T, n, m.nu), bool)
for s in range(1, T):
  for e in range(n):
    d.qpos[:], d.qvel[:] = q[s - 1, e], v[s - 1, e]
    d.ctrl[:] = nat.ctrl_from_action(a[s, e])
    mujoco.mj_fwdPosition(m, d)
    mujoco.mj_fwdVelocity(m, d)
    raw = G * d.ctrl + B0 + B1 * d.actuator_length + B2 * d.actuator_velocity
    sat[s, e] = (raw < FR[:, 0]) | (raw > FR[:, 1])
res = {"what": __doc__.strip().splitlines()[0], "n_envs": int(n)}
for lab, sl in (("0-1 s", slice(1, 50)), ("1-2.5 s", slice(50, 125)), ("2.5-10 s (standing)", slice(125, T))):
  frac = sat[sl].mean(axis=(0, 1))
  res[lab] = {"saturated_actuator_frac_of_actuator_steps": float(sat[sl].mean()),
              "per_actuator_frac_top": {names[i]: round(float(frac[i]), 3) for i in np.argsort(-frac)[:6] if frac[i] > 0},
              "forcerange_of_top": {names[i]: float(FR[i, 1]) for i in np.argsort(-frac)[:3] if frac[i] > 0}}
print(json.dumps(res, indent=1))
(OUT / "getup_satnames.json").write_text(json.dumps(res, indent=1))
