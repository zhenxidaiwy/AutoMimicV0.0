"""Save selected frames of a backflip side-by-side video as PNG grids for a visual check (crouch, take-off, flight,
landing, end). Usage: python peek_flip_video.py [r14] -> sim2sim/logs/peek_backflip_<r>_{a,b}.png
"""
import sys
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

r = sys.argv[1] if len(sys.argv) > 1 else "r14"
p = Path(__file__).resolve().parent.parent / "videos" / "sim2sim" / f"backflip_{r}_side_by_side.mp4"
fr = imageio.mimread(p, memtest=False)
print(len(fr), fr[0].shape)
sets = {"a": [60, 92, 99, 104, 108], "b": [112, 116, 120, 124, 188]}
for k, idx in sets.items():
  idx = [min(i, len(fr) - 1) for i in idx]
  img = np.concatenate([fr[i][::2, ::2] for i in idx], axis=0)
  out = Path(__file__).resolve().parent / "logs" / f"peek_backflip_{r}_{k}.png"
  imageio.imwrite(out, img)
  print("frames", idx, "->", out)
