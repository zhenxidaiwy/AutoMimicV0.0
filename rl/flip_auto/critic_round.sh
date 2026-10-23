#!/usr/bin/env bash
# critic_round.sh <run dir> <ckpt tag e.g. model_5500> <round>: run the critic on a harness eval record (no frames)
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
EV=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$1/eval
python critic.py $EV/flip_auto_$2_record.npz ~/projects/dance/dataset/backflip_3/labels_50fps.npz --round $3 | head -n 75
python3 - "$EV/flip_auto_$2_record.npz" <<'EOF'
import sys, numpy as np
R = np.load(sys.argv[1], allow_pickle=True)
fz = R["foot_z"]; jn = [str(x) for x in R["joint_names"]]; q = R["q"]
print("foot z (m) every 4 steps from 116: step L R | knee L R | hip_pitch L R | hip_roll L R | sh_roll L R")
ix = {n: jn.index(n) for n in jn}
for t in range(116, len(fz), 4):
  g = lambda n: q[t, ix[n]]
  print(t, f"{fz[t,0]:.2f} {fz[t,1]:.2f} | {g('left_knee_joint'):+.2f} {g('right_knee_joint'):+.2f} | "
        f"{g('left_hip_pitch_joint'):+.2f} {g('right_hip_pitch_joint'):+.2f} | {g('left_hip_roll_joint'):+.2f} "
        f"{g('right_hip_roll_joint'):+.2f} | {g('left_shoulder_roll_joint'):+.2f} {g('right_shoulder_roll_joint'):+.2f}")
EOF
