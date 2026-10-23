import importlib.util as u
import os
import platform

import mujoco

print(platform.system(), {m: bool(u.find_spec(m)) for m in ("onnxruntime", "torch", "mujoco")},
      "mujoco", mujoco.__version__, "cpus", os.cpu_count())
