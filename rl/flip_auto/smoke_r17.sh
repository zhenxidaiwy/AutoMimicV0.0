#!/usr/bin/env bash
# smoke_r17.sh: 2-iteration check that the r17 draft (held reference + dyn_base_still) loads; not a training round
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
cd ~/dance_win/rl/flip_auto || exit 1
DS=~/projects/dance/dataset/backflip_3
python - <<'EOF'
import json, library as l
d = json.load(open("decisions/r17.json"))
fixes = l.active_fixes(l.load(), "backflip_3") + d["knobs"]["extra_dyn"]
json.dump(fixes, open("/tmp/dyn_smoke17.json", "w")); print(len(fixes), "dyn terms, last:", fixes[-1]["name"])
EOF
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_hold_50fps.npz --flip-rewards 2 --dyn-rewards /tmp/dyn_smoke17.json \
  --knee-limit 120 --delay-ms 25 -- --motion-file $DS/g1_ballistic_hold_50fps.npz --env.scene.num-envs 128 --agent.max-iterations 2 \
  --agent.run-name smoke_r17 --agent.logger tensorboard 2>&1 | grep -E "base_still|Traceback|Error|Learning iteration 1/" | cut -c 1-300
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_smoke_r17
