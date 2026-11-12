"""Which joints move while the robot should hold still? Per joint velocity RMS over a step window of an eval record,
pelvis fore/aft vs lateral motion (heading frame) and the dominant sway period.
Usage: python sway_joints.py <record.npz> <first step> [last step]"""
import sys

import numpy as np

R = np.load(sys.argv[1], allow_pickle=True)
a = int(sys.argv[2])
b = int(sys.argv[3]) if len(sys.argv) > 3 else len(R["q"])
jn = [str(x).replace("_joint", "") for x in R["joint_names"]]
dt = float(R["dt"])
dq = R["dq"][a:b]
rms = np.sqrt((dq ** 2).mean(0))
print(f"window steps {a}-{b} ({(b - a) * dt:.1f} s); joint velocity RMS (rad/s), top 10:")
for j in np.argsort(-rms)[:10]:
  print(f"  {jn[j]:22s} {rms[j]:.3f}   pos range {np.ptp(R['q'][a:b, j]):.3f} rad")
bn = [str(x) for x in R["body_names"]]
p = R["bp"][a:b, bn.index("pelvis") if "pelvis" in bn else 0]
q = R["bq"][a:b, bn.index("pelvis") if "pelvis" in bn else 0]  # wxyz
w, x, y, z = q.mean(0) / np.linalg.norm(q.mean(0))
yaw = np.arctan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z))
fwd, lat = np.array([np.cos(yaw), np.sin(yaw)]), np.array([-np.sin(yaw), np.cos(yaw)])
d = p[:, :2] - p[:, :2].mean(0)
f, l = d @ fwd, d @ lat
print(f"pelvis fore/aft range {np.ptp(f):.3f} m (std {f.std():.3f}), lateral range {np.ptp(l):.3f} m (std {l.std():.3f}), "
      f"net drift fore {f[-1] - f[0]:+.3f} / lat {l[-1] - l[0]:+.3f} m")
sp = np.abs(np.fft.rfft(f - f.mean()))
fr = np.fft.rfftfreq(len(f), dt)
k = 1 + int(np.argmax(sp[1:]))
print(f"dominant fore/aft sway frequency {fr[k]:.2f} Hz (period {1 / fr[k]:.2f} s)")
