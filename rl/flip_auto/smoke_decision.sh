#!/usr/bin/env bash
# smoke_decision.sh K: 2-iteration training with the active library fixes + decisions/rKK.json extra_dyn, to catch
# wrong joint / phase names before a full round
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
cd ~/dance_win/rl/flip_auto || exit 1
K=$(printf %02d $1)
DS=~/projects/dance/dataset/backflip_3
python - "$K" <<'EOF'
import json, sys, library as l
d = json.load(open(f"decisions/r{sys.argv[1]}.json"))
fixes = l.active_fixes(l.load(), "backflip_3") + d["knobs"].get("extra_dyn", [])
json.dump(fixes, open("/tmp/dyn_smoke.json", "w")); print(len(fixes), "dyn terms:", [f["name"] for f in fixes])
EOF
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --flip-rewards 2 --dyn-rewards /tmp/dyn_smoke.json \
  --knee-limit 120 --delay-ms 25 -- --motion-file $DS/g1_ballistic_50fps.npz --env.scene.num-envs 128 --agent.max-iterations 2 \
  --agent.run-name smoke_decision --agent.logger tensorboard 2>&1 | grep -E "library|root_ori|flip_stand|delay|Traceback|Error|Learning iteration 1/" | cut -c 1-300
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_smoke_decision
