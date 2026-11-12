#!/usr/bin/env bash
# contact_repair_check.sh <clip> [contact_lock args]: labels -> contact lock -> geometry + elbow + root-speed checks
source ~/miniforge3/etc/profile.d/conda.sh; conda activate gmr
cd ~/dance_win/scripts/data || exit 1
id=$1; shift
python write_annotation.py $id && python contact_lock.py $id "$@" || exit 1
python ref_contacts.py ~/projects/dance/data/g1/$id/g1_contact_vlm.csv 2
python elbow_check.py g1 $id 4
python - $id <<'EOF'
import sys, numpy as np
from pathlib import Path
c = np.loadtxt(Path.home() / f"projects/dance/data/g1/{sys.argv[1]}/g1_contact_vlm.csv", delimiter=",")
v = np.diff(c[:, :3], axis=0) * 30
print("root speed max m/s: vertical %.2f horizontal %.2f; joint speed max rad/s %.1f" %
      (np.abs(v[:, 2]).max(), np.linalg.norm(v[:, :2], axis=1).max(), (np.abs(np.diff(c[:, 7:], axis=0)) * 30).max()))
EOF
