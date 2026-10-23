"""Render a figure SVG to PDF (vector, for LaTeX) and PNG (preview): python render_fig.py fig_main.svg
Images referenced as href="fig_assets/x.jpg" are embedded as base64 (cairosvg does not load the relative files);
the self-contained SVG is also written as <name>_embedded.svg."""
import base64
import re
import sys
from pathlib import Path

import cairosvg

src = Path(sys.argv[1]).resolve()
text = src.read_text(encoding="utf-8")


def embed(m):
  p = src.parent / m.group(1)
  mime = "image/png" if p.suffix.lower() == ".png" else "image/jpeg"
  return f'href="data:{mime};base64,{base64.b64encode(p.read_bytes()).decode()}"'


text = re.sub(r'href="(fig_assets/[^"]+)"', embed, text)
emb = src.with_name(src.stem + "_embedded.svg")
emb.write_text(text, encoding="utf-8")
cairosvg.svg2pdf(bytestring=text.encode(), write_to=str(src.with_suffix(".pdf")))
cairosvg.svg2png(bytestring=text.encode(), write_to=str(src.with_suffix(".png")), output_width=3200)
print("wrote", src.with_suffix(".pdf"), src.with_suffix(".png"), emb)
