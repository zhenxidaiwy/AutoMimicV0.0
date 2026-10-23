"""Probe the Bilibili view API once (diagnose rate limiting)."""
import json
import urllib.error
import urllib.request

if __name__ == "__main__":
    url = "https://api.bilibili.com/x/web-interface/view?aid=117321108558028"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://www.bilibili.com/"})
    try:
        with urllib.request.urlopen(req, timeout=15) as f:
            d = json.load(f)
        print("code", d.get("code"), d.get("message"), (d.get("data") or {}).get("title"))
    except urllib.error.HTTPError as e:
        print("HTTP", e.code, e.reason)
