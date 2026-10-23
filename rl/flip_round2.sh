#!/usr/bin/env bash
# Backflip optimisation round, long version: train each variant ITERS iterations (default 3000; the user judged 1000
# too few for this task), evaluate the checkpoints at every 1000 iterations with eval_flip.py and append each to
# ~/projects/dance_logs/flip_rounds.tsv (tag gets @<iter>).
# Usage: ITERS=3000 bash flip_round2.sh <round> <clip> <variant npz> "<tag>|<train_dance.py extra args>" ...
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
R=$1; clip=$2; var=$3; shift 3
IT=${ITERS:-3000}
DS=~/projects/dance/dataset/$clip; L=~/projects/dance_logs; T=$L/flip_rounds.tsv
[ -f $T ] || echo -e "round\ttag\tclip\tvariant\targs\tref_rot\trobot_rot\tmax_rot\tref_peak\trobot_peak\tairborne_s\tlanded\tvideo" > $T
for spec in "$@"; do
  tag=${spec%%|*}; extra=${spec#*|}
  run=${clip}_${var}_${tag}
  echo "=== $R $run [$extra] $IT iters $(date +%T)"
  es=$(echo "$extra" | grep -oP '(?<=--effort-scale )[0-9.]+' || true)
  python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz $extra -- \
    --motion-file $DS/g1_${var}_50fps.npz --env.scene.num-envs 4096 --agent.max-iterations $IT \
    --agent.run-name $run --agent.logger tensorboard > $L/train_$run.log 2>&1
  grep -E "\[train_dance\]" $L/train_$run.log | cut -c 1-200
  dir=$(ls -d ~/projects/dance/runs/logs/rsl_rl/*/*_$run | tail -1)
  for k in $(seq 1000 1000 $IT); do
    ck=model_$((k - 1)).pt; [ -f $dir/$ck ] || ck=model_$k.pt; [ -f $dir/$ck ] || continue
    r=$(EFFORT=${es:-1.0} bash ~/dance_win/rl/eval_flip.sh $run $clip $var $ck)
    echo "@$k $(echo "$r" | cut -c 1-330)"
    echo "$r" | python -c "
import json, sys
j = json.loads(sys.stdin.read())
print('\t'.join(map(str, ['$R', '$tag@$k', '$clip', '$var', '''$extra''', j['ref_rotation_deg'], j['robot_rotation_deg'],
      j['robot_max_rotation_deg'], j['ref_peak_pelvis_m'], j['robot_peak_pelvis_m'], j['robot_airborne_s'],
      j['landed_upright'], j['video']])))" >> $T
  done
done
echo ROUND_DONE
