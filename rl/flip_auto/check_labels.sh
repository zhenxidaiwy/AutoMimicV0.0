#!/usr/bin/env bash
# check_labels.sh: phase vocabulary of the backflip labels vs flip_rewards.PHASES
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
python - <<'EOF'
import numpy as np
z = np.load("/home/user/projects/dance/dataset/backflip_3/labels_50fps.npz")
print("files:", z.files)
print("phase_names:", [str(x) for x in z["phase_names"]])
print("PHASES     :", ["stand", "crouch", "takeoff", "flight", "land", "settle", "other"])
print("len", len(z["phase"]), "unique ids", sorted(set(z["phase"].tolist())))
EOF
