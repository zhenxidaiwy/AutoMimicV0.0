#!/usr/bin/env bash
# ref_audit.sh <task> [round]: ref_phase_stats + ref_term_audit on the task's training reference, with the term_*
# knobs of that round's decision (default: built-in defaults)
export AUTOMIMIC_TASK=$1
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
cd ~/dance_win/rl/flip_auto || exit 1
eval "$(python3 -c "
import taskcfg as t
print(f'DS={t.DS}; VAR={t.VAR}; LAB={t.LABELS}')")"
python ref_phase_stats.py $DS/g1_${VAR}_50fps.npz $DS/$LAB
T=$(python3 -c "
import json, taskcfg as t
r = [x for x in json.load(open(t.STATE))['rounds'] if x['round'] == int('${2:-0}')] if '$2' else []
print(json.dumps(r[0]['knobs'].get('terms', {}) if r else {}))")
echo "terms: $T"
python ref_term_audit.py $DS/g1_${VAR}_50fps.npz $DS/$LAB "$T"
