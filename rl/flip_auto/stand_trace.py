"""After-landing trace from an eval record: phase label, pelvis xy drift from the touchdown spot, pelvis speed, feet
height, tilt. Usage: python3 stand_trace.py <record.npz> <labels.npz> [first=120] [step=3]"""
import sys

import numpy as np

R = np.load(sys.argv[1], allow_pickle=True)
L = np.load(sys.argv[2])
a = int(sys.argv[3]) if len(sys.argv) > 3 else 120
s = int(sys.argv[4]) if len(sys.argv) > 4 else 3
names = [str(x) for x in L["phase_names"]]
ph = L["phase"]
bn = [str(x) for x in R["body_names"]]
bp, fz, dt = R["bp"], R["foot_z"], float(R["dt"])
pel = bp[:, bn.index("pelvis") if "pelvis" in bn else 0]
T = len(pel)
print(f"{len(ph)} label frames, {T} steps; phase runs:",
      [(names[ph[i]], i) for i in range(len(ph)) if i == 0 or ph[i] != ph[i - 1]])
p0 = pel[a, :2]
print("step phase      drift_m  speed_m/s  footL  footR")
for t in range(a, T, s):
  v = np.linalg.norm(pel[t, :2] - pel[max(t - 1, 0), :2]) / dt
  print(f"{t:4d} {names[ph[min(t, len(ph) - 1)]]:9s} {np.linalg.norm(pel[t, :2] - p0):8.3f} {v:9.2f} {fz[t, 0]:6.2f} {fz[t, 1]:6.2f}")
