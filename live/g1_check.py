"""Windows: load the G1 live scene (MuJoCo cannot open non-ASCII absolute paths -> chdir + relative path)."""
import os
import time
from pathlib import Path

import mujoco

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent / "g1")
    m = mujoco.MjModel.from_xml_path("scene_live.xml")
    d = mujoco.MjData(m)
    print("mujoco", mujoco.__version__, "nq", m.nq, "njnt", m.njnt)
    print([m.joint(i).name for i in range(m.njnt)])
    r = mujoco.Renderer(m, 480, 480)
    mujoco.mj_forward(m, d)
    t0 = time.time()
    for _ in range(50):
        r.update_scene(d)
        img = r.render()
    print(f"render {1000 * (time.time() - t0) / 50:.1f} ms/frame", img.shape)
