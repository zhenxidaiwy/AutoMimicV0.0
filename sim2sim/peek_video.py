"""Save a few frames of the side-by-side videos as one PNG strip for a visual check.
Usage: python peek_video.py  -> ~/dance_win/sim2sim/logs/peek_<clip>.png
"""
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

D = Path(__file__).resolve().parent.parent / "videos" / "sim2sim"
for clip in ("sss", "gxdsm"):
  p = D / f"{clip}_side_by_side.mp4"
  if not p.exists():
    continue
  fr = imageio.mimread(p, memtest=False)
  idx = np.linspace(0, len(fr) - 1, 4).astype(int)
  strip = np.concatenate([fr[i][::2, ::2] for i in idx], axis=0)
  out = Path(__file__).resolve().parent / "logs" / f"peek_{clip}.png"
  imageio.imwrite(out, strip)
  print(clip, len(fr), fr[0].shape, "->", out)
