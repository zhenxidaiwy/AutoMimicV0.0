"""Fetch Bilibili metadata / html5 mp4 via the mobile page (desktop page + API are 412 risk-controlled).

Usage:
  python -I unseen_fetch.py meta <aid> [<aid> ...]          -> TSV lines: av<aid> dur views owner title url_ok
  python -I unseen_fetch.py get <out_dir> <aid> [<aid> ...] -> <out_dir>/av<aid>.mp4 + av<aid>.meta.json
Personal research use only (held-out test videos); nothing is uploaded.
"""
import http.cookiejar
import json
import os
import re
import sys
import time
import urllib.request

UA_M = ("Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1")
CJ = http.cookiejar.CookieJar()
OPENER = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CJ))


def _get(url, headers=None, timeout=30):
    req = urllib.request.Request(url, headers={"User-Agent": UA_M, **(headers or {})})
    return OPENER.open(req, timeout=timeout)


def warm():
    try:
        _get("https://m.bilibili.com/", timeout=15).read()
    except Exception as e:  # cookies are best-effort
        print("warm failed:", e, file=sys.stderr)


def vid(x):
    """'BV1...' stays as is, a bare number becomes 'av<number>'."""
    return x if x.startswith("BV") else f"av{x}"


def state(aid):
    html = _get(f"https://m.bilibili.com/video/{vid(aid)}").read().decode("utf-8", "replace")
    i = html.find("__INITIAL_STATE__=")
    if i < 0:
        return None, html
    s = html[i + len("__INITIAL_STATE__="):]
    try:
        obj, _ = json.JSONDecoder().raw_decode(s)
    except Exception:
        obj = None
    return obj, html


def find_info(obj, html):
    info = {"title": None, "duration": None, "owner": None, "views": None, "mp4": None, "w": None, "h": None,
            "real_aid": None}

    def walk(o):
        if isinstance(o, dict):
            if info["title"] is None and isinstance(o.get("title"), str) and "owner" in o:
                info["title"] = o["title"]
                info["real_aid"] = o.get("aid")
                info["duration"] = o.get("duration")
                info["owner"] = (o.get("owner") or {}).get("name")
                info["views"] = (o.get("stat") or {}).get("view")
                d = o.get("dimension") or {}
                info["w"], info["h"] = d.get("width"), d.get("height")
            for v in o.values():
                walk(v)
        elif isinstance(o, list):
            for v in o:
                walk(v)

    if obj is not None:
        walk(obj)
    m = re.search(r'"url":"(https:[^"]*?\.mp4\?[^"]*)"', html)
    if m:
        info["mp4"] = m.group(1).replace("\\u002F", "/").replace("\\u0026", "&")
    if info["title"] is None:
        t = re.search(r"<title[^>]*>([^<]*)</title>", html)
        info["title"] = t.group(1).replace("_哔哩哔哩_bilibili", "") if t else None
    return info


def main():
    mode = sys.argv[1]
    warm()
    if mode == "meta":
        for aid in sys.argv[2:]:
            try:
                obj, html = state(aid)
                info = find_info(obj, html)
                print(f"{vid(aid)}\tav{info['real_aid']}\t{info['duration']}\t{info['views']}\t{info['owner']}\t"
                      f"{info['w']}x{info['h']}\t{'mp4' if info['mp4'] else 'nomp4'}\t{info['title']}", flush=True)
            except Exception as e:
                print(f"av{aid}\tNA\tNA\tNA\tNA\tERR\t{e}", flush=True)
            time.sleep(1.0)
    elif mode == "get":
        out = os.path.expanduser(sys.argv[2])
        os.makedirs(out, exist_ok=True)
        for aid in sys.argv[3:]:
            dst = os.path.join(out, f"av{aid}.mp4")
            if os.path.exists(dst) and os.path.getsize(dst) > 0:
                print("exists", dst, flush=True)
                continue
            try:
                obj, html = state(aid)
                info = find_info(obj, html)
                if aid.startswith("BV") and info["real_aid"]:  # always store files under the numeric av id
                    aid = str(info["real_aid"])
                    dst = os.path.join(out, f"av{aid}.mp4")
                if not info["mp4"]:
                    print(f"av{aid}: no mp4 url")
                    continue
                if info["duration"] and info["duration"] > 300:
                    print(f"av{aid}: too long ({info['duration']} s), skipped")
                    continue
                tmp = dst + ".part"
                # the CDN often ends the stream early -> resume with HTTP Range until Content-Length is reached
                want, got = 0, 0
                open(tmp, "wb").close()
                for attempt in range(12):
                    hdr = {"Referer": "https://m.bilibili.com/"}
                    if got:
                        hdr["Range"] = f"bytes={got}-"
                    try:
                        r = _get(info["mp4"], headers=hdr, timeout=60)
                    except Exception as e:
                        print(f"av{aid}: request error {e}", flush=True)
                        time.sleep(2)
                        continue
                    if not want:
                        want = int(r.headers.get("Content-Length") or 0)
                    if got and r.status != 206:  # server ignored Range -> restart
                        got = 0
                        open(tmp, "wb").close()
                    with open(tmp, "ab") as f:
                        try:
                            while True:
                                b = r.read(1 << 20)
                                if not b:
                                    break
                                f.write(b)
                        except Exception as e:
                            print(f"av{aid}: read error {e}", flush=True)
                    got = os.path.getsize(tmp)
                    if want == 0 or got >= want:
                        break
                    print(f"av{aid}: partial {got}/{want}, resume {attempt + 1}", flush=True)
                else:
                    print(f"av{aid}: FAIL incomplete after 12 tries", flush=True)
                    os.remove(tmp)
                    continue
                os.replace(tmp, dst)
                info["aid"] = aid
                info["url"] = f"https://www.bilibili.com/video/av{aid}"
                info.pop("mp4")
                json.dump(info, open(os.path.join(out, f"av{aid}.meta.json"), "w", encoding="utf-8"),
                          ensure_ascii=False, indent=1)
                print(f"av{aid}: ok {os.path.getsize(dst) / 1e6:.1f} MB  {info['title']}", flush=True)
            except Exception as e:
                print(f"av{aid}: FAIL {e}", flush=True)
            time.sleep(1.5)


if __name__ == "__main__":
    main()
