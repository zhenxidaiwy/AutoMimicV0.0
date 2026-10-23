"""Print the conventions of a training keypoint cache (j3d_cam axes / units, K, image size)."""
import sys
from pathlib import Path

import numpy as np

k = np.load(Path.home() / "projects/dance/vla/kp" / f"{sys.argv[1] if len(sys.argv) > 1 else 'bda_zhao_sss'}.npz")
print({n: k[n].shape for n in k.files})
j = k["j3d_cam"]
print("K", k["K"].round(1).tolist(), "wh", k["img_wh"])
print("mean nose", j[:, 0].mean(0).round(2), "mean mid-hip", ((j[:, 11] + j[:, 12]) / 2).mean(0).round(2),
      "mean mid-ankle", ((j[:, 15] + j[:, 16]) / 2).mean(0).round(2))
print("height (ankle-nose, m)", np.linalg.norm(j[:, 0] - (j[:, 15] + j[:, 16]) / 2, axis=-1).mean().round(2))
