#!/usr/bin/env bash
# Tracker ceiling: the canonical 闪身步 clip played continuously (no person), robot vs reference ankle spread.
O=~/projects/dance_logs/follow_analysis; mkdir -p $O
bash ~/dance_win/live/server.sh --bench gym_sss --bench_seconds 14 --playback oracle --rec $O/oracle.npz 2>&1 | \
  grep -E "done:|Error|Traceback|line [0-9]+," | cut -c1-160
~/miniforge3/envs/gmr/bin/python - <<'EOF'
import numpy as np
from pathlib import Path
z = np.load(Path.home() / "projects/dance_logs/follow_analysis/oracle.npz")
R = z["rec"]
t, rob, ref = R[:, 0], np.abs(R[:, 4]), np.abs(R[:, 6])
k = t > 1.0
print(f"oracle playback {t[-1]:.1f} s: reference spread median {np.median(ref[k]):.2f} max {ref[k].max():.2f} m | "
      f"robot spread median {np.median(rob[k]):.2f} max {rob[k].max():.2f} m")
for q in (50, 90, 99):
  print(f"  p{q}: reference {np.percentile(ref[k], q):.2f} m  robot {np.percentile(rob[k], q):.2f} m")
# also the raw columns 5/7 (fore-aft) in case the flash is mostly fore-aft in this frame
print(f"  fore-aft |dx| p90: reference {np.percentile(np.abs(R[k, 7]), 90):.2f}  robot {np.percentile(np.abs(R[k, 5]), 90):.2f}")
EOF
