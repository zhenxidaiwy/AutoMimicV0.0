"""Search Bilibili for candidate dance clips (metadata only, nothing downloaded).

Step 1: yt-dlp `bilisearchN:` gives video ids (cached in ids.json; retries with backoff on HTTP 412).
Step 2: `yt-dlp -j --skip-download` per id fills title / duration / uploader / views / resolution.
        (The plain web API returns 412 without browser cookies; yt-dlp handles signing.)
Rows are appended to candidates_meta.jsonl as they arrive, so the run can be resumed.

Usage (gmr env): python search_bili.py [N per query]
"""
import json
import os
import subprocess
import sys
import time

QUERIES = ["闪身步", "闪身步 教学", "闪身步 花鼓灯", "花鼓灯 闪身步 赵铁春", "闪身步 翻跳", "闪身步 挑战",
           "闪身步 舞蹈", "狗熊哆嗦毛"]
OUT = os.path.expanduser("~/projects/dance/data/search")
YTDLP = [sys.executable, "-m", "yt_dlp", "--no-warnings"]


def search_ids(query, n):
    for attempt in range(4):
        r = subprocess.run(YTDLP + ["--flat-playlist", "-j", f"bilisearch{n}:{query}"], capture_output=True, text=True)
        ids = [json.loads(l)["id"] for l in r.stdout.splitlines() if l.strip()]
        if ids:
            return ids
        time.sleep(15 * (attempt + 1))
    return []


def video_meta(aid):
    r = subprocess.run(YTDLP + ["-j", "--skip-download", f"https://www.bilibili.com/video/av{aid}"],
                       capture_output=True, text=True, timeout=120)
    lines = [l for l in r.stdout.splitlines() if l.startswith("{")]
    if not lines:
        return None, r.stderr.strip().splitlines()[-1:] or ["no output"]
    d = json.loads(lines[0])
    return {"aid": aid, "bvid": d.get("display_id") or d.get("id"), "title": d.get("title"),
            "duration": int(d.get("duration") or 0), "owner": d.get("uploader"), "views": d.get("view_count") or 0,
            "width": d.get("width"), "height": d.get("height"), "url": d.get("webpage_url"),
            "desc": (d.get("description") or "")[:200]}, None


if __name__ == "__main__":
    n = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    os.makedirs(OUT, exist_ok=True)
    ids_path, meta_path = f"{OUT}/ids.json", f"{OUT}/candidates_meta.jsonl"
    if os.path.exists(ids_path):
        hits = json.load(open(ids_path))
    else:
        hits = {}
        for q in QUERIES:
            ids = search_ids(q, n)
            print(f"{q}: {len(ids)} ids", flush=True)
            for i in ids:
                hits.setdefault(i, []).append(q)
            time.sleep(8)
        json.dump(hits, open(ids_path, "w"), ensure_ascii=False)
    done = set()
    if os.path.exists(meta_path):
        done = {json.loads(l)["aid"] for l in open(meta_path, encoding="utf-8")}
    print(f"{len(hits)} unique ids, {len(done)} already have metadata", flush=True)
    fails = 0
    with open(meta_path, "a", encoding="utf-8") as f:
        for k, (aid, qs) in enumerate(hits.items()):
            if aid in done:
                continue
            m, err = video_meta(aid)
            if m:
                m["queries"] = qs
                f.write(json.dumps(m, ensure_ascii=False) + "\n")
                f.flush()
            else:
                fails += 1
                print(f"[{k}] {aid} failed: {err}", flush=True)
                time.sleep(10)
            if k % 20 == 0:
                print(f"progress {k}/{len(hits)}", flush=True)
            time.sleep(1.0)
    print(f"done, failures {fails}")
