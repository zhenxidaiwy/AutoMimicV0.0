"""Collect Bilibili BV ids for queries from the server-rendered search pages (the search API is 412-blocked).

Usage: python -I unseen_search.py <out.txt> <query> [<query> ...]
Appends "BVxxxx<TAB>query" lines (deduplicated across queries) to out.txt.
"""
import http.cookiejar
import os
import re
import sys
import time
import urllib.parse
import urllib.request

UA_D = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0 Safari/537.36")
OP = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA_D, "Accept-Encoding": "identity",
                                               "Referer": "https://www.bilibili.com/"})
    try:
        with OP.open(req, timeout=20) as r:
            return r.read().decode("utf-8", "replace")
    except Exception as e:
        print("ERR", url, e)
        return ""


if __name__ == "__main__":
    out = os.path.expanduser(sys.argv[1])
    seen = set()
    if os.path.exists(out):
        seen = {l.split("\t")[0] for l in open(out, encoding="utf-8")}
    get("https://www.bilibili.com/")
    with open(out, "a", encoding="utf-8") as f:
        for q in sys.argv[2:]:
            k = urllib.parse.quote(q)
            n_new = 0
            for page in (1, 2):
                html = get(f"https://search.bilibili.com/video?keyword={k}&page={page}")
                for bv in dict.fromkeys(re.findall(r"BV1[0-9A-Za-z]{9}", html)):
                    if bv not in seen:
                        seen.add(bv)
                        f.write(f"{bv}\t{q}\n")
                        n_new += 1
                time.sleep(2)
            print(f"{q}: {n_new} new", flush=True)
    print("total", len(seen))
