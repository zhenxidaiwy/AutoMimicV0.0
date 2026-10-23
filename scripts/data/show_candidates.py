"""Print Bilibili candidates sorted by views. Usage: python show_candidates.py [max_seconds]"""
import json
import os
import sys

if __name__ == "__main__":
    max_s = int(sys.argv[1]) if len(sys.argv) > 1 else 10**9
    p = os.path.expanduser("~/projects/dance/data/search/candidates_meta.jsonl")
    rows = [json.loads(l) for l in open(p, encoding="utf-8")]
    rows = [r for r in rows if r["duration"] <= max_s]
    for r in sorted(rows, key=lambda r: -r["views"]):
        print(f'{r["bvid"]:<13} {r["duration"]//60:>2}:{r["duration"]%60:02d} {r["views"]:>9} '
              f'{r["width"]}x{r["height"]:<5} {r["owner"][:10]:<10} {r["title"][:50]}')
    print(len(rows), "rows")
