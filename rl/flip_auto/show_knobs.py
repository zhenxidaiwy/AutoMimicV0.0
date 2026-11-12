"""Print the knobs currently in the harness state (what the next round inherits)."""
import json
from pathlib import Path

st = json.loads((Path(__file__).resolve().parent / "state.json").read_text())
k = st["knobs"]
print(json.dumps({x: k[x] for x in k if x != "extra_dyn"}, indent=0)[:1500])
for d in k.get("extra_dyn", []):
  print(json.dumps(d))
print("best", st["best"])
