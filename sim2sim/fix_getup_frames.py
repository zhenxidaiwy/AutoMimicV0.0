"""Dump a few frames of the regenerated get-up side-by-side video to out/fix_frames/ for a visual check."""
from pathlib import Path

import imageio.v2 as imageio

HERE = Path(__file__).resolve().parent
r = imageio.get_reader(str(HERE.parent / "videos" / "sim2sim" / "getup_side_by_side.mp4"))
meta = r.get_meta_data()
frames = [f for f in r]
print("frames", len(frames), "fps", meta.get("fps"), "size", frames[0].shape)
out = HERE / "out" / "fix_frames"
out.mkdir(parents=True, exist_ok=True)
for i in (0, 30, 150, 151, 302, 453, len(frames) - 1):
  if i < len(frames):
    imageio.imwrite(out / f"getup_f{i:04d}.png", frames[i])
print("wrote", out)
