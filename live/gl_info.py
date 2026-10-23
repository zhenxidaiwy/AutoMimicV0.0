"""Which GPU does MuJoCo's OpenGL context use on Windows? Also time a 2nd batch of renders (excludes warm-up)."""
import os
import time
from pathlib import Path

import mujoco
from OpenGL import GL

if __name__ == "__main__":
    os.chdir(Path(__file__).resolve().parent / "g1")
    m = mujoco.MjModel.from_xml_path("scene_live.xml")
    d = mujoco.MjData(m)
    r = mujoco.Renderer(m, 480, 480)
    mujoco.mj_forward(m, d)
    r.update_scene(d)
    r.render()
    print("GL_VENDOR  ", GL.glGetString(GL.GL_VENDOR).decode())
    print("GL_RENDERER", GL.glGetString(GL.GL_RENDERER).decode())
    for n in (20, 50):
        t0 = time.time()
        for _ in range(n):
            r.update_scene(d)
            r.render()
        print(f"{n} renders: {1000 * (time.time() - t0) / n:.1f} ms/frame")
