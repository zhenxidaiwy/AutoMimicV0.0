"""Tilt / pelvis / knees / arm over the last steps of an eval: python3 tail_table.py <steps.tsv> [first step]"""
import csv
import sys

rows = list(csv.DictReader(open(sys.argv[1]), delimiter="\t"))
a = int(sys.argv[2]) if len(sys.argv) > 2 else 120
print("columns:", ", ".join(rows[0].keys())[:400])
keys = [k for k in rows[0] if any(s in k for s in ("tilt", "pelvis_z", "feet_d", "roll", "yaw", "knee"))][:8]
print("step " + " ".join(f"{k[:12]:>12s}" for k in keys))
for r in rows:
  t = int(float(r.get("step", r.get("t", 0))))
  if t >= a and t % 4 == 0:
    print(f"{t:4d} " + " ".join(f"{float(r[k]):12.3f}" for k in keys))
