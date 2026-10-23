"""Crop the figure thumbnails from paper/fig_assets/raw (relative boxes l,t,r,b in [0,1]) -> fig_assets/*.jpg,
plus a check sheet fig_assets/crops_check.jpg."""
from pathlib import Path

from PIL import Image

D = Path(__file__).resolve().parent / "fig_assets"
R = D / "raw"
CROPS = {  # name: (source, (l, t, r, b) relative to the source image)
  "human_flip": ("human_66", (0.40, 0.16, 0.74, 0.70)),
  "smpl_tuck": ("smpl_66", (0.62, 0.05, 0.92, 0.75)),
  "g1_retarget": ("qa_66", (0.66, 0.12, 0.86, 0.56)),
  "roll_82": ("eval_82", (0.30, 0.25, 0.75, 0.80)),
  "roll_95": ("eval_95", (0.30, 0.20, 0.75, 0.80)),
  "roll_108": ("eval_108", (0.15, 0.10, 0.85, 0.65)),
  "roll_126": ("eval_126", (0.25, 0.25, 0.75, 0.85)),
  "fail_101": ("eval_101", (0.10, 0.20, 0.80, 0.80)),
}
out = []
for name, (src, (l, t, r, b)) in CROPS.items():
  im = Image.open(R / f"{src}.jpg").convert("RGB")
  w, h = im.size
  c = im.crop((int(l * w), int(t * h), int(r * w), int(b * h)))
  c.save(D / f"{name}.jpg", quality=92)
  out.append(c.resize((int(c.width * 260 / c.height), 260)))
sheet = Image.new("RGB", (sum(o.width for o in out), 260), "white")
x = 0
for o in out:
  sheet.paste(o, (x, 0))
  x += o.width
sheet.save(D / "crops_check.jpg", quality=85)
print({n: Image.open(D / f"{n}.jpg").size for n in CROPS})
