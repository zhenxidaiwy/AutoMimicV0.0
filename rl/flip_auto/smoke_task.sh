#!/usr/bin/env bash
# smoke_task.sh <task>: 2-iteration training with that task's reference, labels, hand friction, delay and terms, to
# catch config errors before a real round
export AUTOMIMIC_TASK=$1
source ~/miniforge3/etc/profile.d/conda.sh; conda activate unitree_rl_mjlab
export MUJOCO_GL=egl MESA_D3D12_DEFAULT_ADAPTER_NAME=NVIDIA WANDB_CONSOLE=off
cd ~/dance_win/rl/flip_auto || exit 1
eval "$(python3 -c "
import taskcfg as t
print(f'DS={t.DS}; VAR={t.VAR}; LAB={t.LABELS}')")"
python ~/dance_win/rl/train_dance.py --rsi phase --labels $DS/$LAB --flip-rewards 2 --knee-limit 120 --delay-ms 25 \
  --hand-friction 0.6 --flip-terms '{"term_stand_fail": {"max_d": 0.85, "max_tilt": 40.0}}' \
  -- --motion-file $DS/g1_${VAR}_50fps.npz --env.scene.num-envs 128 --agent.max-iterations 2 \
  --agent.run-name smoke_$1 --agent.logger tensorboard 2>&1 | grep -E "hand collision|delay|root_ori|terminations|Traceback|Error|Learning iteration 1/|Mean episode length" | cut -c 1-300
rm -rf ~/projects/dance/runs/logs/rsl_rl/g1_tracking/*_smoke_$1
