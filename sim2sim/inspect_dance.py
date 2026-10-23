"""Quick inspection helper for the dance sim2sim (checkpoint keys, npz layout, model sensors/actuators).
Usage (unitree_rl_mjlab env):  python inspect_dance.py
"""
from pathlib import Path

import mujoco
import numpy as np
import torch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
for tag in ("sss_bda_v1", "gxdsm_full_v1"):
  ck = torch.load(ROOT / "policies" / tag / "policy.pt", weights_only=False, map_location="cpu")
  print(tag, "ckpt keys", list(ck.keys()))
  for k, v in ck.items():
    if isinstance(v, dict):
      for kk, vv in v.items():
        print("  ", k, kk, tuple(vv.shape) if torch.is_tensor(vv) else type(vv))
      break
  z = np.load(ROOT / "policies" / tag / "reference_motion.npz")
  print(tag, "npz", {k: z[k].shape for k in z.files}, "fps" in z.files and z["fps"])
m = mujoco.MjModel.from_binary_path(str(HERE / "models" / "dance.mjb"))
print("opt", m.opt.timestep, m.opt.integrator, m.opt.cone, m.opt.solver, m.opt.iterations, m.opt.ls_iterations,
      m.opt.tolerance, m.opt.ls_tolerance, m.opt.impratio, "disableflags", m.opt.disableflags, "enable", m.opt.enableflags)
print("nsensor", m.nsensor, [(m.sensor(i).name, int(m.sensor_type[i]), int(m.sensor_dim[i]), int(m.sensor_adr[i])) for i in range(m.nsensor)])
print("ctrllimited", m.actuator_ctrllimited.tolist(), "forcelimited", m.actuator_forcelimited.tolist()[:3])
print("dyntype", m.actuator_dyntype.tolist()[:3], "gaintype", m.actuator_gaintype.tolist()[:3], "biastype", m.actuator_biastype.tolist()[:3])
print("trnid", m.actuator_trnid[:, 0].tolist())
print("joints", [(m.joint(i).name, int(m.jnt_qposadr[i]), int(m.jnt_dofadr[i])) for i in range(m.njnt)])
print("bodies", [m.body(i).name for i in range(m.nbody)])
print("ngeom", m.ngeom, "nmesh", m.nmesh, "nhfield", m.nhfield, "ntex", m.ntex)
