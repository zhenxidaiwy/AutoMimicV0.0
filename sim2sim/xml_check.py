"""Dev check: does models/getup.xml compile (with native_getup.load_model's fixes) and match models/getup.mjb?
Usage: python xml_check.py   (any env with mujoco + numpy; the mjb comparison needs MuJoCo 3.5)
"""
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import mujoco  # noqa: E402
from native_getup import FP_FIELDS, load_model  # noqa: E402

m = load_model(HERE / "models" / "getup.xml")
print("mujoco", mujoco.__version__, "xml model: nq", m.nq, "nv", m.nv, "nu", m.nu, "ngeom", m.ngeom, "nbody", m.nbody)
try:
  r = mujoco.MjModel.from_binary_path(str(HERE / "models" / "getup.mjb"))
  for f in FP_FIELDS:
    a, b = np.asarray(getattr(m, f), float), np.asarray(getattr(r, f), float)
    print(f, "max|diff|", float(np.max(np.abs(a - b))) if a.shape == b.shape else f"shape {a.shape} vs {b.shape}")
  print("opt equal:", str(m.opt) == str(r.opt))
except Exception as e:  # noqa: BLE001
  print("mjb compare skipped:", e)
