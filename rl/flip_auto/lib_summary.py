"""Print the diagnostic library for the decider: active fixes, custom entries, and the latest severity of each check.
Usage: python3 lib_summary.py [filter substring]"""
import json
import sys
from pathlib import Path

lib = json.loads((Path(__file__).resolve().parent / "library.json").read_text())
flt = sys.argv[1] if len(sys.argv) > 1 else ""
print(len(lib["checks"]), "checks")
for c in lib["checks"]:
  if flt and flt not in c["id"]:
    continue
  h = c.get("history", [])
  last = h[-1]["severity"] if h else None
  fix = c.get("fix") or {}
  if c.get("weight", 0) > 0 or c["kind"] == "custom" or flt:
    print(f"{c['id']:45s} w={c.get('weight', 0):<5} last_sev={last} fix={json.dumps(fix)[:110]}")
