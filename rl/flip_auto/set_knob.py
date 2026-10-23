"""Set harness knobs in state.json between rounds (harness stopped):
python set_knob.py terms.term_hip_extended.max_hip=0.0 weights.flip_tuck=3.0 ..."""
import json
import sys
from pathlib import Path

p = Path(__file__).resolve().parent / "state.json"
st = json.loads(p.read_text())
for a in sys.argv[1:]:
  path, val = a.split("=", 1)
  keys = path.split(".")
  d = st["knobs"]
  for k in keys[:-1]:
    d = d.setdefault(k, {})
  d[keys[-1]] = json.loads(val)
  print("set", path, "=", d[keys[-1]])
p.write_text(json.dumps(st, indent=1))
