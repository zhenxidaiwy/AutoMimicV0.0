"""CPU cost of native MuJoCo stepping for the G1 scene (sim2sim resource estimate) + a torch-CPU MLP of the
policy's size. Usage: python step_bench.py"""
import os
import time
from pathlib import Path

import mujoco
import numpy as np

os.chdir(Path(__file__).resolve().parent / "g1")
m = mujoco.MjModel.from_xml_path("scene_live.xml")
d = mujoco.MjData(m)
m.opt.timestep = 0.005
d.qpos[2] = 0.3  # lying-ish: many contacts (worst case for the get-up)
mujoco.mj_forward(m, d)
n = 4000
t0 = time.perf_counter()
for _ in range(n):
  d.ctrl[:] = np.random.uniform(-0.2, 0.2, m.nu) if m.nu else 0
  mujoco.mj_step(m, d)
dt = (time.perf_counter() - t0) / n
print(f"mujoco {mujoco.__version__}: mj_step {dt * 1e3:.3f} ms (nu={m.nu}, contacts at end {d.ncon}) -> "
      f"real time needs 200 steps/s = {200 * dt * 100:.1f}% of one core")

import torch  # noqa: E402
net = torch.nn.Sequential(torch.nn.Linear(154, 512), torch.nn.ELU(), torch.nn.Linear(512, 256), torch.nn.ELU(),
                          torch.nn.Linear(256, 128), torch.nn.ELU(), torch.nn.Linear(128, 29)).eval()
torch.set_num_threads(1)
x = torch.zeros(1, 154)
with torch.no_grad():
  for _ in range(50):
    net(x)
  t0 = time.perf_counter()
  for _ in range(1000):
    net(x)
pt = (time.perf_counter() - t0) / 1000
print(f"policy MLP (154-512-256-128-29) on 1 CPU thread: {pt * 1e3:.3f} ms -> 50 Hz needs {50 * pt * 100:.1f}% of one core")
