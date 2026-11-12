"""Print the structure of a 50 fps reference npz and its phase labels (frames per phase run, rest tail length).
Usage: python inspect_ref.py <ref.npz> <labels.npz>"""
import sys

import numpy as np

z = np.load(sys.argv[1])
print({k: z[k].shape for k in z.files})
print("fps", z["fps"] if "fps" in z.files else "-")
L = np.load(sys.argv[2])
names = [str(x) for x in L["phase_names"]]
ph = L["phase"]
runs, s = [], 0
for i in range(1, len(ph) + 1):
  if i == len(ph) or ph[i] != ph[s]:
    runs.append((names[ph[s]], s, i - 1))
    s = i
print("frames", len(ph), "runs", runs)
print("label files", L.files)
print("last frame joint_vel max", float(np.abs(z["joint_vel"][-1]).max()))
