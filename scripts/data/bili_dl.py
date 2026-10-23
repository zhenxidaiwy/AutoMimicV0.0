"""Bilibili download through the public web API (no login, no cookies): view API -> cid, playurl API (DASH,
best video <= 720p + best audio) -> ffmpeg merge. Fallback for yt-dlp's 'Unable to extract initial state'.
Personal research only. Usage: python bili_dl.py <BVid> <out.mp4> [--probe]"""
import json
import subprocess
import sys
import time
import urllib.request

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Referer": "https://www.bilibili.com/"}


import http.cookiejar

# anonymous visitor cookies (buvid3 etc., no account): the API answers 412 without them
_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def get(url):
  with _opener.open(urllib.request.Request(url, headers=H), timeout=30) as r:
    return r.read()


get("https://www.bilibili.com/")


bv, out = sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None
v = json.loads(get(f"https://api.bilibili.com/x/web-interface/view?bvid={bv}"))
if v.get("code") != 0:
  sys.exit(f"view API: {v.get('code')} {v.get('message')}")
d = v["data"]
cid = d["cid"]
print(bv, d["title"], d["duration"], "s", "cid", cid)
p = json.loads(get(f"https://api.bilibili.com/x/player/playurl?bvid={bv}&cid={cid}&qn=64&fnval=16&fourk=0"))
if p.get("code") != 0:
  sys.exit(f"playurl API: {p.get('code')} {p.get('message')}")
dash = p["data"]["dash"]
vids = sorted([x for x in dash["video"] if x.get("height", 0) <= 720], key=lambda x: (x["height"], x["bandwidth"]))
vid = vids[-1] if vids else dash["video"][0]
aud = max(dash.get("audio") or [{}], key=lambda x: x.get("bandwidth", 0))
print("video", vid["height"], vid.get("codecs"), "audio", aud.get("bandwidth"))
if "--probe" in sys.argv or not out:
  sys.exit(0)
tmp_v, tmp_a = out + ".v.m4s", out + ".a.m4s"
for url, f in ((vid["baseUrl"], tmp_v), (aud.get("baseUrl"), tmp_a)):
  if url:
    open(f, "wb").write(get(url))
    time.sleep(1)
args = ["ffmpeg", "-loglevel", "error", "-y", "-i", tmp_v] + (["-i", tmp_a] if aud.get("baseUrl") else []) + ["-c", "copy", out]
subprocess.run(args, check=True)
subprocess.run(["rm", "-f", tmp_v, tmp_a])
json.dump(d, open(out.rsplit(".", 1)[0] + ".info.json", "w"), ensure_ascii=False)
print("saved", out)
