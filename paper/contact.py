"""Contact sheet of paper/fig_assets/raw/*.jpg (each scaled to height 220, labelled with file name and size)."""
from pathlib import Path

from PIL import Image, ImageDraw

D = Path(__file__).resolve().parent / "fig_assets/raw"
ims = []
for p in sorted(D.glob("*.jpg")):
  im = Image.open(p)
  w, h = im.size
  t = im.resize((int(w * 220 / h), 220))
  ImageDraw.Draw(t).text((5, 5), f"{p.stem} {w}x{h}", fill=(255, 255, 0))
  ims.append(t)
rows, row, x = [], [], 0
for t in ims:
  if x + t.width > 2400 and row:
    rows.append(row)
    row, x = [], 0
  row.append(t)
  x += t.width
rows.append(row)
H = 220 * len(rows)
sheet = Image.new("RGB", (2400, H), "black")
for r, row in enumerate(rows):
  x = 0
  for t in row:
    sheet.paste(t, (x, r * 220))
    x += t.width
sheet.save(D.parent / "contact.jpg", quality=85)
print(len(ims), "images ->", D.parent / "contact.jpg")
