#!/usr/bin/env bash
# End-to-end test of the library loop on round 7's record: init -> critic -> grow -> active fixes -> 2-iter training
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
cd ~/dance_win/rl/flip_auto || exit 1
EV=~/projects/dance/runs/logs/rsl_rl/g1_tracking/2026-10-23_00-20-46_flipauto_r07/eval
DS=~/projects/dance/dataset/backflip_3
echo "== 1 task init"; python task_init.py backflip_3 ballistic
echo "== 2 critic"; python critic.py $EV/flip_hd_model_5000_record.npz $DS/labels_50fps.npz --round 7 | sed -n '1,12p'
echo "== 3 grow"
python -c "
import json, harness
crit = json.load(open('$EV/flip_hd_model_5000_critic.json'))
ch, esc = harness.grow_library(crit, 7)
print(len(ch), 'changes'); print('\n'.join(ch[:14])); print('escalate:', json.dumps(esc[:5], indent=0)[:900])
"
echo "== 4 active fixes"
python -c "
import json, library as l
f = l.active_fixes(l.load()); json.dump(f, open('/tmp/dyn_test.json', 'w')); print(len(f), [d['name'] for d in f])
"
echo "== 5 training smoke"
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/labels_50fps.npz --flip-rewards 2 --dyn-rewards /tmp/dyn_test.json \
  --knee-limit 120 -- --motion-file $DS/g1_ballistic_50fps.npz --env.scene.num-envs 128 --agent.max-iterations 2 \
  --agent.run-name smoke_library --agent.logger tensorboard 2>&1 | grep -E "library fixes|Traceback|Error|Learning iteration 1/" | cut -c 1-400
