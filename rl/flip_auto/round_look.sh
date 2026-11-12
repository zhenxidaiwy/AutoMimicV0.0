#!/usr/bin/env bash
# round_look.sh <task> <round> <ckpt>: step-2 helpers in one go - floor contacts (robot vs reference), ankle heights in
# the first stand and around the landing, the labelled foot contacts there, and full-resolution close-ups 0-131
export AUTOMIMIC_TASK=$1; R=$2; C=$3
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
bash contacts_round.sh $1 $R $C 0 130 | head -16
run=$(python3 -c "import taskcfg; print(taskcfg.run_name($R))")
rec=$(ls ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_${run}/eval/flip_auto_${C}_record.npz | head -1)
python ankle_z.py "$rec" 0 18 | awk 'NR==1||NR%3==2'
python ankle_z.py "$rec" 80 116 | awk 'NR==1||NR%3==2'
LAB=$(python3 -c "
import json, taskcfg as t
r = [x for x in json.load(open(t.STATE))['rounds'] if x['round'] == $R][0]
print(t.DS / r['knobs'].get('reference', {}).get('labels', t.LABELS))")
python - "$LAB" <<'EOF'
import sys, numpy as np
L = np.load(sys.argv[1])
names = [str(x) for x in L["phase_names"]]
for a, b in ((0, 20), (78, 118)):
  print(f"labels {a}-{b - 1}: phase", [names[p] for p in L["phase"][a:b:4]])
  print("  contact_L", L["contact_L"][a:b].tolist())
  print("  contact_R", L["contact_R"][a:b].tolist())
EOF
cd ~/dance_win
V=$(ls videos/${1}/auto/r$(printf %02d $R)/r$(printf %02d $R)_${C}.mp4)
bash rl/flip_auto/closeup.sh "$V" videos/${1}/auto/r$(printf %02d $R)/close/c 0 131 | tail -1
