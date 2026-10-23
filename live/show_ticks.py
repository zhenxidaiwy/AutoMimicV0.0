"""Print the offline recognition ticks of one video: python show_ticks.py <watch> <video> [t0] [t1]"""
import json
import sys
from pathlib import Path

t = json.load(open(Path.home() / "projects/dance/vla/trigger_eval" / sys.argv[1] / "ticks.json"))[sys.argv[2]]
t0, t1 = (float(sys.argv[3]), float(sys.argv[4])) if len(sys.argv) > 4 else (0, 99)
for x in t:
  if t0 <= x["t"] <= t1:
    print(x["t"], x["vis"] if x["vis"] != "ok" else
          f"d={x['d']} f={x['f']:.0f} conf={x['conf']:.2f} move_p={x['move_p']:.2f} other={x.get('other', 0):.2f}")
