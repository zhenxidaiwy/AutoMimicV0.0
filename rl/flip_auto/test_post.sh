#!/usr/bin/env bash
# test_post.sh: end-to-end check of the +5 s recording on round 15 (eval -> critic -> robustness), before a round ends
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA
D=~/projects/dance/dataset/backflip_3
RUN=2026-10-23_11-39-43_flipauto_r15; CK=model_13499.pt
d=~/projects/dance/runs/logs/rsl_rl/g1_tracking/$RUN
date +%H:%M
python ~/dance_win/rl/eval_flip.py --ckpt $d/$CK --motion $D/g1_ballistic_hold_50fps.npz --labels $D/labels_hold_50fps.npz \
  --knee-limit 120 --tag posttest --size 960 720 2>&1 | grep -E '^\{|Traceback|Error' | python -c "
import json,sys
t=sys.stdin.read()
try:
  r=json.loads(t.strip().splitlines()[-1]); print('eval clip_s', r['clip_s'], {k:v for k,v in r.items() if k.startswith(('hold_','post_'))}, 'track', r['track_body_err_m'])
except Exception: print(t[:2000])"
ffprobe -v error -show_entries format=duration -of csv=p=0 $d/eval/flip_posttest.mp4
cd ~/dance_win/rl/flip_auto
python critic.py $d/eval/flip_posttest_record.npz $D/labels_hold_50fps.npz --no-library 2>&1 | head -4
MOTION=$D/g1_ballistic_hold_50fps.npz bash robust.sh $RUN $CK nominal,delay1 32
date +%H:%M
