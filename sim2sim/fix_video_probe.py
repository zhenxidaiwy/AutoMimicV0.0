"""FIX stage: probe the regenerated side-by-side videos (frame count, size) and dump a few frames as PNG."""
import json
from pathlib import Path

import imageio.v2 as imageio
import numpy as np

HERE = Path(__file__).resolve().parent
VID = HERE.parent / "videos" / "sim2sim"
OUT = HERE / "fix_frames"
OUT.mkdir(exist_ok=True)
stats = {}
for clip, picks in (("sss", (0, 118, 236)), ("gxdsm", (0, 128, 256))):
  frames = imageio.mimread(VID / f"{clip}_side_by_side.mp4", memtest=False)
  arr = np.stack(frames).astype(np.float32)
  stats[clip] = dict(n_frames=len(frames), shape=list(frames[0].shape),
                     mean_abs_frame_diff_left=float(np.abs(np.diff(arr[:, :, :480], axis=0)).mean()),
                     mean_abs_frame_diff_right=float(np.abs(np.diff(arr[:, :, 480:], axis=0)).mean()))
  for i in picks:
    imageio.imwrite(OUT / f"{clip}_f{i:04d}.png", frames[min(i, len(frames) - 1)])
(OUT / "video_stats.json").write_text(json.dumps(stats, indent=1))
print(json.dumps(stats))
