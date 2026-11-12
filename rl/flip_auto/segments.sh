#!/usr/bin/env bash
# segments.sh <task> <round> <ckpt> [starts]: eval_segments.py on that round's checkpoint with the round's reference,
# hand friction and delay (which parts of the reference are learned?)
export AUTOMIMIC_TASK=$1; R=$2; C=$3
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
cd ~/dance_win/rl/flip_auto || exit 1
eval "$(python3 -c "
import json, taskcfg as t
r = [x for x in json.load(open(t.STATE))['rounds'] if x['round'] == $R][0]
k = r['knobs']; ref = k.get('reference', {})
print(f\"RUN={r['run']}; MOT={t.DS}/g1_{ref.get('variant', t.VAR)}_50fps.npz; LAB={t.DS}/{ref.get('labels', t.LABELS)}; HF={k.get('hand_friction', 0)}; DM={k.get('delay_ms', 0)}\")")"
python ~/dance_win/rl/eval_segments.py --ckpt ~/projects/dance/runs/logs/rsl_rl/g1_tracking/$RUN/$C.pt --motion $MOT \
  --labels $LAB --hand-friction $HF --delay-ms $DM --starts ${4:-0,16,30,46,60,81,95,115} \
  --out ~/projects/dance_logs/segments_${1}_r$(printf %02d $R)_$C.json 2>&1 | grep -E '^\{|Traceback|Error' | cut -c 1-300
