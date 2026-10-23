"""Align every clip's timeline to its dance's canonical clip using the VLM phase / swing labels.

Output per human frame (30 fps): canonical frame index (30 fps, in the canonical clip) -> "skill state".
  闪身步   canonical = bda_zhao_sss. Each cycle (prep→flash→hold→recover→settle) of a clip is mapped to the canonical
           cycle with the same recover foot (C1: R, C2: L), piecewise-linear between phase boundaries.
           Frames outside cycles (stand / ready) -> canonical stand frame. tonyfu_sss_slow ('hold' only) -> C1 hold.
  狗熊哆嗦毛 canonical = bda2_gxdsm_full. Each step unit (swing start -> next swing start) maps to the canonical
           representative unit of the same side (L: 46→58, R: 58→68). Before the first swing: stand / prep;
           after the last swing: settle / stand segments of the canonical clip.
The set of canonical frames that can appear = the model's classes ("skill states").
"""
import json
from pathlib import Path

import numpy as np

DS = Path.home() / "projects/dance/dataset"
CANON = {"闪身步": "bda_zhao_sss", "狗熊哆嗦毛": "bda2_gxdsm_full"}
# canonical 闪身步 cycles (30 fps frames in bda_zhao_sss): anchors a0 cycle start, a1 flash start, a2 recover start,
# a3 settle start, a4 cycle end (exclusive)
SSS_C = {"R": [18, 24, 38, 46, 53], "L": [70, 74, 84, 94, 99]}
SSS_STAND = 60
SSS_HOLD = 34
GX_UNIT = {"L": (46, 58), "R": (58, 68)}
GX_STAND0, GX_PREP, GX_SETTLE, GX_STAND1 = 5, (14, 16), (206, 223), 225


def segments(phase):
  out, s = [], 0
  for t in range(1, len(phase) + 1):
    if t == len(phase) or phase[t] != phase[s]:
      out.append((phase[s], s, t))  # [s, t)
      s = t
  return out


def interp(t, src, dst):
  return float(np.interp(t, src, dst))


def align_sss(ann):
  ph = ann["phase"]
  T = len(ph)
  c = np.full(T, float(SSS_STAND))
  if set(ph) == {"hold"}:
    return np.full(T, float(SSS_HOLD))
  segs = segments(ph)
  i = 0
  while i < len(segs):
    name, s, e = segs[i]
    if name in ("prep", "flash"):
      # collect the cycle: from prep/flash until the end of settle (or the next stand)
      j, a = i, {"a0": s}
      while j < len(segs) and segs[j][0] in ("prep", "flash", "hold", "recover", "settle"):
        n2, s2, e2 = segs[j]
        if n2 == "flash" and "a1" not in a:
          a["a1"] = s2
        if n2 == "recover" and "a2" not in a:
          a["a2"] = s2
        if n2 == "settle" and "a3" not in a:
          a["a3"] = s2
        end = e2
        j += 1
        if n2 == "settle":
          break
      a1 = a.get("a1", a["a0"])
      a2 = a.get("a2", (a1 + end) // 2)
      a3 = a.get("a3", max(a2 + 1, end - 3))
      src = [a["a0"], a1, a2, a3, end]
      # recover foot of this cycle
      side = "R"
      for s_, e_, foot in ann.get("swing", []):
        if a2 <= e_ and s_ < a3:
          side = foot
          break
      dst = SSS_C[side]
      for t in range(a["a0"], end):
        c[t] = interp(t, src, dst)
      i = j
    else:
      i += 1
  return c


def align_gx(ann):
  ph = ann["phase"]
  T = len(ph)
  c = np.full(T, float(GX_STAND0))
  sw = sorted([(s, e, f) for s, e, f in ann.get("swing", [])])
  for t in range(T):
    if ph[t] == "prep":
      c[t] = GX_PREP[0] + 1
    elif ph[t] in ("settle",):
      c[t] = (GX_SETTLE[0] + GX_SETTLE[1]) / 2
  if sw:
    for k, (s, e, f) in enumerate(sw):
      nxt = sw[k + 1][0] if k + 1 < len(sw) else min(e + 4, T)
      u0, u1 = GX_UNIT[f]
      for t in range(s, nxt):
        c[t] = interp(t, [s, nxt], [u0, u1 - 0.01])
    last = sw[-1][1] + 4
    for t in range(min(last, T), T):  # after the last step
      c[t] = (GX_SETTLE[0] + GX_SETTLE[1]) / 2 if ph[t] in ("settle", "shake", "recover", "hold") else GX_STAND1
  # shake frames without any swing nearby (e.g. pure quivering): use the middle of the L unit
  covered = np.zeros(T, bool)
  for s, e, f in sw:
    covered[s:e + 8] = True
  for t in range(T):
    if ph[t] == "shake" and not covered[t] and not sw:
      c[t] = 52
  return c


def align(cid):
  ann = json.load(open(DS / cid / "annotation.json", encoding="utf-8"))
  return (align_sss(ann) if ann["move"] == "闪身步" else align_gx(ann)), ann["move"]


def state_table():
  """All canonical frames that can be targets -> class ids. Returns list of (dance, canonical_frame)."""
  st = [("闪身步", SSS_STAND), ("闪身步", SSS_HOLD)]
  for side in ("R", "L"):
    a0, *_, a4 = SSS_C[side]
    st += [("闪身步", f) for f in range(a0, a4)]
  st += [("狗熊哆嗦毛", GX_STAND0), ("狗熊哆嗦毛", GX_STAND1)] + [("狗熊哆嗦毛", f) for f in range(*GX_PREP)]
  for side in ("L", "R"):
    st += [("狗熊哆嗦毛", f) for f in range(*GX_UNIT[side])]
  st += [("狗熊哆嗦毛", f) for f in range(*GX_SETTLE)]
  st += [("狗熊哆嗦毛", 52)]
  seen, out = set(), []
  for x in st:
    if x not in seen:
      seen.add(x)
      out.append(x)
  return out


def to_class(c, move, table):
  cand = [(i, f) for i, (m, f) in enumerate(table) if m == move]
  ids = np.array([i for i, _ in cand])
  fr = np.array([f for _, f in cand], float)
  return np.array([ids[np.argmin(np.abs(fr - x))] for x in c])


if __name__ == "__main__":
  table = state_table()
  print(f"{len(table)} skill states")
  for cid in ["bda_zhao_sss", "tonyfu_sss_fast", "tonyfu_sss_slow", "tonyfu_sss_single", "street_sss_a", "street_sss_b",
              "street_sss_c", "street_sss_d", "street_sss_e", "bda2_gxdsm_full", "gym_sss", "hoodie_sss",
              "bda_ming_gxdsm_a", "bda_ming_gxdsm_b"]:
    c, move = align(cid)
    k = to_class(c, move, table)
    print(f"{cid:<18} {move:<6} T={len(c):4d} canon range {c.min():5.1f}-{c.max():5.1f}  classes used {len(set(k)):3d}"
          f"  sample: {[int(x) for x in c[::max(1, len(c) // 12)]]}")
