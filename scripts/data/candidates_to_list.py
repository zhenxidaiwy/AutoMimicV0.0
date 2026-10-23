"""Parse data/video_candidates_*.md (video scout output) into a download list: '<motion_slug>\t<url>' per line.
Usage: python candidates_to_list.py <candidates.md> <out.tsv>"""
import re
import sys
from pathlib import Path

md = Path(sys.argv[1]).read_text(encoding="utf-8")
out, motion = [], None
for line in md.splitlines():
  m = re.match(r"^### 3\.\d+ (.+)$", line)
  if m:
    motion = re.sub(r"[^a-z0-9]+", "_", re.sub(r"\(.*?\)", "", m.group(1)).lower()).strip("_")
    continue
  if motion and line.startswith("|"):
    for u in re.findall(r"https://www\.(?:bilibili\.com/video/BV\w+|youtube\.com/watch\?v=[\w-]+)", line):
      out.append(f"{motion}\t{u}")
seen, rows = set(), []
for r in out:
  if r.split("\t")[1] not in seen:
    seen.add(r.split("\t")[1])
    rows.append(r)
Path(sys.argv[2]).write_text("\n".join(rows) + "\n", encoding="utf-8")
print(len(rows), "videos;", len({r.split(chr(9))[0] for r in rows}), "motions")
