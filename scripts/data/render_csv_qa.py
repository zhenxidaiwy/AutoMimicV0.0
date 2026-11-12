"""QA render of any G1 csv variant (same camera as retarget_headless.py): source clip | G1.
Usage (gmr env, MUJOCO_GL=egl): python render_csv_qa.py <clip> <variant stem, e.g. g1_lock_vlm> <out.mp4>"""
import pathlib
import sys

import mujoco
import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from retarget_headless import GMR_ROOT, render_qa  # noqa: E402

clip, var, out = sys.argv[1:4]
D = pathlib.Path.home() / "projects/dance/data"
c = np.loadtxt(D / "g1" / clip / f"{var}.csv", delimiter=",")
q = np.concatenate([c[:, :3], c[:, [6, 3, 4, 5]], c[:, 7:]], 1)
model = mujoco.MjModel.from_xml_path(str(GMR_ROOT / "assets" / "unitree_g1" / "g1_mocap_29dof.xml"))
render_qa(model, q, 30, str(D / "clips" / f"{clip}.mp4"), out)
print(out)
