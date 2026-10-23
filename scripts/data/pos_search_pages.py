"""Like unseen_search.py, but with a configurable page range (env PAGES="1-5", default 1-2).

Usage: PAGES=3-5 python -I pos_search_pages.py <out.txt> <query> [<query> ...]
Appends "BVxxxx<TAB>query" lines (deduplicated across queries and the existing file) to out.txt.
"""
import os
import re
import sys
import time
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from unseen_search import get  # noqa: E402

if __name__ == "__main__":
    out = os.path.expanduser(sys.argv[1])
    a, b = (int(x) for x in os.environ.get("PAGES", "1-2").split("-"))
    seen = set()
    if os.path.exists(out):
        seen = {l.split("\t")[0] for l in open(out, encoding="utf-8")}
    get("https://www.bilibili.com/")
    with open(out, "a", encoding="utf-8") as f:
        for q in sys.argv[2:]:
            k = urllib.parse.quote(q)
            n_new = 0
            for page in range(a, b + 1):
                html = get(f"https://search.bilibili.com/video?keyword={k}&page={page}")
                for bv in dict.fromkeys(re.findall(r"BV1[0-9A-Za-z]{9}", html)):
                    if bv not in seen:
                        seen.add(bv)
                        f.write(f"{bv}\t{q}\n")
                        n_new += 1
                time.sleep(2)
            print(f"{q}: {n_new} new", flush=True)
    print("total", len(seen))
